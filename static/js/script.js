class ToggleSlider {
    constructor(container, targetPage = 'scan.html') {
        this.container = container;
        this.track = container.querySelector('.slider-track');
        this.handle = container.querySelector('.slider-handle');
        this.targetPage = targetPage;
        this.isActive = false;
        this.isDragging = false;
        this.startX = 0;
        this.currentX = 0;
        
        this.init();
    }

    init() {
        // Mouse events
        this.handle.addEventListener('mousedown', (e) => this.startDrag(e));
        document.addEventListener('mousemove', (e) => this.drag(e));
        document.addEventListener('mouseup', () => this.endDrag());

        // Touch events
        this.handle.addEventListener('touchstart', (e) => this.startDrag(e), { passive: false });
        document.addEventListener('touchmove', (e) => this.drag(e), { passive: false });
        document.addEventListener('touchend', () => this.endDrag());

        // Click to toggle
        this.track.addEventListener('click', (e) => this.handleClick(e));

        // Prevent text selection
        this.container.addEventListener('selectstart', (e) => e.preventDefault());
    }

    startDrag(e) {
        this.isDragging = true;
        this.startX = e.type === 'mousedown' ? e.clientX : e.touches[0].clientX;
        this.handle.style.cursor = 'grabbing';
        this.handle.style.transform = 'scale(1.1)';
        
        if (e.type === 'touchstart') {
            e.preventDefault();
        }
    }

    drag(e) {
        if (!this.isDragging) return;

        e.preventDefault();
        this.currentX = e.type === 'mousemove' ? e.clientX : e.touches[0].clientX;
        const deltaX = this.currentX - this.startX;
        const trackWidth = this.track.offsetWidth;
        const handleWidth = this.handle.offsetWidth;
        const maxPosition = trackWidth - handleWidth - 20;

        let newPosition = this.isActive ? maxPosition + deltaX : deltaX;
        
        // Constrain position
        newPosition = Math.max(10, Math.min(maxPosition, newPosition));
        
        // Update handle position
        this.handle.style.left = newPosition + 'px';
        this.handle.style.transition = 'none';
        
        // Update track background based on position
        const progress = (newPosition - 10) / (maxPosition - 10);
        this.updateTrackProgress(progress);
    }

    endDrag() {
        if (!this.isDragging) return;
        
        this.isDragging = false;
        this.handle.style.cursor = 'grab';
        this.handle.style.transform = 'scale(1)';
        this.handle.style.transition = 'all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
        
        const trackWidth = this.track.offsetWidth;
        const handleWidth = this.handle.offsetWidth;
        const currentPosition = parseInt(this.handle.style.left) || 10;
        const maxPosition = trackWidth - handleWidth - 20;
        const threshold = maxPosition * 0.6;

        if (currentPosition > threshold) {
            this.activate();
        } else {
            this.deactivate();
        }
    }

    handleClick(e) {
        if (this.isDragging) return;
        
        const rect = this.track.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const trackWidth = rect.width;
        
        if (clickX > trackWidth / 2) {
            this.activate();
        } else {
            this.deactivate();
        }
    }

    activate() {
        this.isActive = true;
        this.track.classList.add('active');
        
        const trackWidth = this.track.offsetWidth;
        const handleWidth = this.handle.offsetWidth;
        const maxPosition = trackWidth - handleWidth - 20;
        
        this.handle.style.left = maxPosition + 'px';
        this.updateTrackProgress(1);
        
        // Navigate after animation completes
        setTimeout(() => {
            this.navigateToPage();
        }, 500);
    }

    deactivate() {
        this.isActive = false;
        this.track.classList.remove('active');
        this.handle.style.left = '10px';
        this.updateTrackProgress(0);
    }

    updateTrackProgress(progress) {
        const percentage = progress * 100;
        this.track.style.setProperty('--progress', percentage + '%');
    }

    navigateToPage() {
        window.location.href = this.targetPage;
    }
}

// Initialize sliders
document.addEventListener('DOMContentLoaded', () => {
    const mainContainer = document.querySelector('.slider-container');
    if (mainContainer) {
        new ToggleSlider(mainContainer, 'scan.html');
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const hamburger = document.querySelector('.hamburger');
    const nav = document.querySelector('.nav');

    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        nav.classList.toggle('active');
    });

    // Handle contact link click
    const contactLink = nav.querySelector('a[href="#contact"]');
    if (contactLink) {
        contactLink.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Close the mobile menu
            hamburger.classList.remove('active');
            nav.classList.remove('active');

            // Small delay to allow menu to close
            setTimeout(() => {
                // Scroll to contact section
                const contactSection = document.getElementById('contact');
                if (contactSection) {
                    contactSection.scrollIntoView({ 
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }, 300);
        });
    }

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!hamburger.contains(e.target) && !nav.contains(e.target)) {
            hamburger.classList.remove('active');
            nav.classList.remove('active');
        }
    });

    // Close menu when clicking other links
    nav.querySelectorAll('a:not([href="#contact"])').forEach(link => {
        link.addEventListener('click', () => {
            hamburger.classList.remove('active');
            nav.classList.remove('active');
        });
    });
});

