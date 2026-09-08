import { animate, inView, scroll, stagger, spring } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm";

document.addEventListener('DOMContentLoaded', () => {
    // ----------------------------------------------------
    // 1. Mobile navigation toggle
    // ----------------------------------------------------
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    const navLinksItems = document.querySelectorAll('.nav-links a');

    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', () => {
            menuToggle.classList.toggle('active');
            navLinks.classList.toggle('active');
        });

        navLinksItems.forEach(item => {
            item.addEventListener('click', () => {
                menuToggle.classList.remove('active');
                navLinks.classList.remove('active');
            });
        });
    }

    // ----------------------------------------------------
    // 2. Navbar scroll effect
    // ----------------------------------------------------
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // ----------------------------------------------------
    // 3. Motion: Reading Progress Bar
    // ----------------------------------------------------
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        scroll(animate(progressBar, { scaleX: [0, 1] }));
    }

    // ----------------------------------------------------
    // 4. Motion: Hero Parallax
    // ----------------------------------------------------
    const mainTitle = document.querySelector('.main-title');
    const subtitle = document.querySelector('.subtitle');
    const heroDesc = document.querySelector('.hero-content .description');

    if (mainTitle) scroll(animate(mainTitle, { y: [0, -150], opacity: [1, 0] }), { offset: ["start start", "end start"] });
    if (subtitle) scroll(animate(subtitle, { y: [0, -100], opacity: [1, 0] }), { offset: ["start start", "end start"] });
    if (heroDesc) scroll(animate(heroDesc, { y: [0, -50], opacity: [1, 0] }), { offset: ["start start", "end start"] });

    // ----------------------------------------------------
    // 5. Motion: Scroll Animations (Replacing IntersectionObserver)
    // ----------------------------------------------------
    inView(".fade-in", (el) => {
        animate(el, { opacity: [0, 1], y: [30, 0] }, { duration: 0.8, ease: [0.16, 1, 0.3, 1] });
    });

    const grids = document.querySelectorAll('.other-projects-grid');
    grids.forEach(grid => {
        inView(grid, () => {
            const cards = grid.querySelectorAll('.project-card');
            // reset their css opacity just in case
            cards.forEach(c => c.style.opacity = 0);
            animate(
                cards,
                { opacity: [0, 1], y: [30, 0] },
                { delay: stagger(0.1), duration: 0.8, ease: [0.16, 1, 0.3, 1] }
            );
        });
    });

    // ----------------------------------------------------
    // 6. Motion: Tactile Spring Hovers
    // ----------------------------------------------------
    const buttons = document.querySelectorAll('.btn-dark, .btn-outline, .cta-button, .cta-button-solid, .project-card');
    
    buttons.forEach(btn => {
        btn.addEventListener('mouseenter', () => {
            animate(btn, { scale: 1.05 }, { type: 'spring', stiffness: 400, damping: 20 });
        });
        btn.addEventListener('mouseleave', () => {
            animate(btn, { scale: 1 }, { type: 'spring', stiffness: 400, damping: 20 });
        });
        btn.addEventListener('mousedown', () => {
            animate(btn, { scale: 0.95 }, { type: 'spring', stiffness: 400, damping: 20 });
        });
        btn.addEventListener('mouseup', () => {
            animate(btn, { scale: 1.05 }, { type: 'spring', stiffness: 400, damping: 20 });
        });
    });

    // ----------------------------------------------------
    // 7. Theme logic
    // ----------------------------------------------------
    const themeToggle = document.getElementById('theme-toggle');
    const systemPrefersLight = window.matchMedia('(prefers-color-scheme: light)').matches;
    let savedTheme = null;
    try {
        savedTheme = localStorage.getItem('theme');
    } catch (error) {}
    
    const moonIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>';
    const sunIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';

    const updateThemeIcon = (theme) => {
        if (themeToggle) {
            animate(themeToggle, { rotate: [0, 180] }, { duration: 0.3 });
            themeToggle.innerHTML = theme === 'light' ? sunIcon : moonIcon;
        }
    };

    if (savedTheme === 'light' || (!savedTheme && systemPrefersLight)) {
        document.documentElement.setAttribute('data-theme', 'light');
        updateThemeIcon('light');
    } else {
        updateThemeIcon('dark');
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            updateThemeIcon(newTheme);
            try {
                localStorage.setItem('theme', newTheme);
            } catch (e) {}
        });
    }
});
