"""
Twitter PC アウトリーチ Bot
===========================
遠藤照明の製品情報を元に、Twitter/X上でPC関連の照明に興味があるユーザーへ
リプライでアウトリーチを行うボット。

403 Forbidden 対策:
- リトライ（指数バックオフ）
- 権限不足の検出と明確なエラーメッセージ
- Quote Tweet へのフォールバック
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import tweepy
from dotenv import load_dotenv

# ── ログ設定 ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("twitter_outreach.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ── 環境変数の読み込み ─────────────────────────────────────
load_dotenv()

REQUIRED_ENV_VARS = [
    "TWITTER_API_KEY",
    "TWITTER_API_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_TOKEN_SECRET",
    "TWITTER_BEARER_TOKEN",
]


def validate_env() -> dict[str, str]:
    """環境変数のバリデーション。不足があれば終了する。"""
    env = {}
    missing = []
    for var in REQUIRED_ENV_VARS:
        val = os.getenv(var)
        if not val:
            missing.append(var)
        else:
            env[var] = val
    if missing:
        logger.error(
            "必要な環境変数が設定されていません: %s\n"
            "→ .env ファイルを確認してください。\n"
            "→ 権限変更後は Access Token の再生成が必要です。",
            ", ".join(missing),
        )
        sys.exit(1)
    return env


# ── Twitter クライアント初期化 ──────────────────────────────
def create_client(env: dict[str, str]) -> tweepy.Client:
    """OAuth 1.0a User Context でクライアントを作成する。"""
    client = tweepy.Client(
        bearer_token=env["TWITTER_BEARER_TOKEN"],
        consumer_key=env["TWITTER_API_KEY"],
        consumer_secret=env["TWITTER_API_SECRET"],
        access_token=env["TWITTER_ACCESS_TOKEN"],
        access_token_secret=env["TWITTER_ACCESS_TOKEN_SECRET"],
        wait_on_rate_limit=True,
    )
    return client


# ── 検索クエリ ─────────────────────────────────────────────
SEARCH_QUERIES = [
    '"オフィス照明" OR "デスクライト" OR "PC照明" -is:retweet lang:ja',
    '"モニターライト" OR "作業照明" OR "LED照明 おすすめ" -is:retweet lang:ja',
]

# ── リプライテンプレート ──────────────────────────────────────
REPLY_TEMPLATES = [
    (
        "PC作業の照明環境、大事ですよね！\n"
        "遠藤照明では目に優しいデスク周りの照明をご提案しています。\n"
        "よろしければご覧ください 👇\n"
        "https://www.endo-lighting.co.jp/"
    ),
    (
        "照明でPC作業の快適さが変わりますよ！\n"
        "遠藤照明のLEDなら省エネ＆目に優しい光を実現できます。\n"
        "詳しくはこちら 👇\n"
        "https://www.endo-lighting.co.jp/"
    ),
]

# ── 送信済み管理 ────────────────────────────────────────────
SENT_LOG_PATH = Path("outreach_sent.json")


def load_sent_ids() -> set[str]:
    """送信済みツイートIDを読み込む。"""
    if SENT_LOG_PATH.exists():
        data = json.loads(SENT_LOG_PATH.read_text(encoding="utf-8"))
        return set(data)
    return set()


def save_sent_ids(sent_ids: set[str]) -> None:
    """送信済みツイートIDを保存する。"""
    SENT_LOG_PATH.write_text(
        json.dumps(sorted(sent_ids), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ── 403 エラー対策付きリプライ送信 ──────────────────────────
MAX_RETRIES = 3
BACKOFF_BASE = 2  # 秒


class ReplyError(Exception):
    """リプライ送信に関するエラー。"""


def send_reply_with_retry(
    client: tweepy.Client,
    text: str,
    in_reply_to_tweet_id: str,
) -> str | None:
    """
    リプライを送信する。403 の場合はリトライ + フォールバックを試みる。

    Returns:
        成功時: ツイートID
        失敗時: None
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.create_tweet(
                text=text,
                in_reply_to_tweet_id=in_reply_to_tweet_id,
            )
            tweet_id = response.data["id"]
            logger.info(
                "リプライ送信成功 (attempt %d): tweet_id=%s → reply_id=%s",
                attempt,
                in_reply_to_tweet_id,
                tweet_id,
            )
            return tweet_id

        except tweepy.Forbidden as e:
            logger.warning(
                "403 Forbidden (attempt %d/%d): %s",
                attempt,
                MAX_RETRIES,
                e,
            )

            if attempt < MAX_RETRIES:
                wait = BACKOFF_BASE ** attempt
                logger.info("  %d秒後にリトライします...", wait)
                time.sleep(wait)
            else:
                logger.error(
                    "403 エラーが解消しません。以下を確認してください:\n"
                    "  1. X Developer Portal でアプリの権限が "
                    "「Read and Write」になっているか\n"
                    "  2. アプリの種類が「Web App, Automation App or Bot」"
                    "になっているか\n"
                    "  3. 権限変更後に Access Token を再生成したか\n"
                    "  4. X Developer Console 自体がダウンしていないか "
                    "(https://status.x.com/)"
                )
                # フォールバック: Quote Tweet を試みる
                return _fallback_quote_tweet(
                    client, text, in_reply_to_tweet_id
                )

        except tweepy.TooManyRequests:
            logger.warning("レート制限に達しました。60秒待機します...")
            time.sleep(60)

        except tweepy.TwitterServerError as e:
            logger.warning("Twitter サーバーエラー: %s。30秒後にリトライ...", e)
            time.sleep(30)

    return None


def _fallback_quote_tweet(
    client: tweepy.Client,
    text: str,
    original_tweet_id: str,
) -> str | None:
    """
    リプライが403で失敗した場合、Quote Tweetで代替する。
    Quote Tweet は in_reply_to を使わないため、権限要件が異なる場合がある。
    """
    logger.info("フォールバック: Quote Tweet を試みます...")
    quote_url = f"https://twitter.com/i/status/{original_tweet_id}"
    quote_text = f"{text}\n{quote_url}"

    try:
        response = client.create_tweet(text=quote_text)
        tweet_id = response.data["id"]
        logger.info(
            "Quote Tweet フォールバック成功: reply_id=%s", tweet_id
        )
        return tweet_id
    except tweepy.Forbidden:
        logger.error(
            "Quote Tweet も 403 Forbidden です。\n"
            "→ Write 権限自体が無効です。トークンを再生成してください。"
        )
        return None
    except Exception as e:
        logger.error("Quote Tweet フォールバック失敗: %s", e)
        return None


# ── メインパイプライン ────────────────────────────────────────
def search_targets(client: tweepy.Client, max_results: int = 10) -> list[dict]:
    """検索クエリに基づいて対象ツイートを取得する。"""
    targets = []
    for query in SEARCH_QUERIES:
        try:
            response = client.search_recent_tweets(
                query=query,
                max_results=min(max_results, 100),
                tweet_fields=["author_id", "created_at", "conversation_id"],
            )
            if response.data:
                for tweet in response.data:
                    targets.append(
                        {
                            "id": str(tweet.id),
                            "text": tweet.text,
                            "author_id": str(tweet.author_id),
                            "created_at": str(tweet.created_at),
                        }
                    )
                logger.info(
                    "クエリ「%s」: %d件取得", query[:40], len(response.data)
                )
        except Exception as e:
            logger.error("検索エラー (query=%s): %s", query[:40], e)
    return targets


def run_outreach(dry_run: bool = False, max_replies: int = 5) -> None:
    """アウトリーチのメインループ。"""
    env = validate_env()
    client = create_client(env)

    # 自分のユーザー情報を取得
    try:
        me = client.get_me()
        logger.info("認証ユーザー: @%s (id=%s)", me.data.username, me.data.id)
    except Exception as e:
        logger.error(
            "認証エラー: %s\n→ APIキーとトークンが正しいか確認してください。", e
        )
        sys.exit(1)

    sent_ids = load_sent_ids()
    targets = search_targets(client)

    if not targets:
        logger.info("対象ツイートが見つかりませんでした。")
        return

    reply_count = 0
    for target in targets:
        if reply_count >= max_replies:
            logger.info("最大リプライ数 (%d) に達しました。", max_replies)
            break

        tweet_id = target["id"]
        if tweet_id in sent_ids:
            logger.debug("スキップ (送信済み): %s", tweet_id)
            continue

        # テンプレートをローテーション
        template = REPLY_TEMPLATES[reply_count % len(REPLY_TEMPLATES)]

        if dry_run:
            logger.info("[DRY RUN] リプライ先: %s / 内容: %s", tweet_id, template[:50])
            sent_ids.add(tweet_id)
            reply_count += 1
            continue

        result = send_reply_with_retry(client, template, tweet_id)
        if result:
            sent_ids.add(tweet_id)
            reply_count += 1
            # レート制限対策: リプライ間に間隔を空ける
            time.sleep(10)
        else:
            logger.warning("リプライ失敗: %s — 次のターゲットへ", tweet_id)

    save_sent_ids(sent_ids)
    logger.info(
        "完了: %d件リプライ送信 / 累計送信済み %d件",
        reply_count,
        len(sent_ids),
    )


# ── エントリーポイント ──────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Twitter PC アウトリーチ Bot"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際には投稿せず、対象ツイートの確認のみ行う",
    )
    parser.add_argument(
        "--max-replies",
        type=int,
        default=5,
        help="1回の実行で送信する最大リプライ数 (default: 5)",
    )
    args = parser.parse_args()

    logger.info("=== Twitter PC アウトリーチ Bot 開始 ===")
    logger.info("  dry_run=%s, max_replies=%d", args.dry_run, args.max_replies)

    run_outreach(dry_run=args.dry_run, max_replies=args.max_replies)

    logger.info("=== 完了 ===")
