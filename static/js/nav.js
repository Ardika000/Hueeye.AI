document.addEventListener('DOMContentLoaded', () => {
    const hamburger = document.querySelector('.hamburger');
    const nav = document.querySelector('.nav-links');

    if (hamburger && nav) {
        // Toggle menu
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('active');
            nav.classList.toggle('active');
            document.body.style.overflow = nav.classList.contains('active') ? 'hidden' : '';
        });

        // Handle contact link click
        const contactLink = nav.querySelector('a[href="#contact"]');
        if (contactLink) {
            contactLink.addEventListener('click', (e) => {
                e.preventDefault();
                
                // If we're not on about.html, navigate to index.html#contact
                if (!window.location.pathname.includes('index.html')) {
                    window.location.href = 'about.html#contact';
                    return;
                }

                // If we're on about.html, scroll to contact section
                const contactSection = document.querySelector('.footer');
                if (contactSection) {
                    // Close hamburger menu
                    hamburger.classList.remove('active');
                    nav.classList.remove('active');
                    document.body.style.overflow = '';

                    // Scroll to contact
                    contactSection.scrollIntoView({ behavior: 'smooth' });
                }
            });
        }

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (nav.classList.contains('active') && 
                !hamburger.contains(e.target) && 
                !nav.contains(e.target)) {
                hamburger.classList.remove('active');
                nav.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }
});