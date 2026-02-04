/**
 * ENDO LIGHTING - JOBサポート UIモック
 * JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const mainNav = document.querySelector('.main-nav');

    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', function() {
            mainNav.classList.toggle('active');
            this.classList.toggle('active');
        });
    }

    // Tab switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            tabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // View toggle (grid/list)
    const viewBtns = document.querySelectorAll('.view-btn');
    viewBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            viewBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Checkbox for product comparison
    const productCheckboxes = document.querySelectorAll('.product-checkbox input');
    const compareBar = document.querySelector('.compare-bar');

    if (productCheckboxes.length > 0 && compareBar) {
        productCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const checkedCount = document.querySelectorAll('.product-checkbox input:checked').length;
                if (checkedCount > 0) {
                    compareBar.style.display = 'block';
                    compareBar.querySelector('strong').textContent = checkedCount;
                } else {
                    compareBar.style.display = 'none';
                }
            });
        });
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            }
        });
    });

    // Pattern buttons (auto-layout page)
    const patternBtns = document.querySelectorAll('.pattern-btn');
    patternBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            patternBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Distance buttons (wall-lighting page)
    const distanceBtns = document.querySelectorAll('.distance-btn');
    distanceBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            distanceBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Beam buttons (wall-lighting page)
    const beamBtns = document.querySelectorAll('.beam-btn');
    beamBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            beamBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Viewer tabs (wall-lighting page)
    const viewerTabs = document.querySelectorAll('.viewer-tab');
    viewerTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            viewerTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // IFC tabs
    const ifcTabs = document.querySelectorAll('.ifc-tab');
    ifcTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            ifcTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Toolbar buttons (section-view page)
    const toolbarBtns = document.querySelectorAll('.toolbar-btn');
    toolbarBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            toolbarBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Dropdown hover effect for desktop
    const navItems = document.querySelectorAll('.nav-item.has-dropdown');
    navItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.querySelector('.dropdown').style.display = 'block';
        });
        item.addEventListener('mouseleave', function() {
            this.querySelector('.dropdown').style.display = '';
        });
    });

    // Form validation placeholder
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Form submitted');
        });
    });

    // Button click feedback
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            // Add ripple effect or feedback
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = '';
            }, 100);
        });
    });

    console.log('ENDO LIGHTING Mock UI loaded successfully');
});
