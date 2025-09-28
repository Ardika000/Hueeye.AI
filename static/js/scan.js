class ReverseSlider {
    constructor(container, targetPage = '/') {
        this.container = container;
        this.track = container.querySelector('.slider-track');
        this.handle = container.querySelector('.slider-handle');
        this.targetPage = targetPage;
        this.isActive = false;
        this.isDragging = false;
        this.startX = 0;
        this.currentX = 0;
        
        // Start from right side for reverse slider
        this.handle.style.left = 'calc(100% - 178px)';
        
        this.init();
    }

    init() {
        this.handle.addEventListener('mousedown', (e) => this.startDrag(e));
        document.addEventListener('mousemove', (e) => this.drag(e));
        document.addEventListener('mouseup', () => this.endDrag());

        this.handle.addEventListener('touchstart', (e) => this.startDrag(e), { passive: false });
        document.addEventListener('touchmove', (e) => this.drag(e), { passive: false });
        document.addEventListener('touchend', () => this.endDrag());

        this.track.addEventListener('click', (e) => this.handleClick(e));
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

        // Reverse the position calculation
        let newPosition = this.isActive ? deltaX : maxPosition + deltaX;
        newPosition = Math.max(10, Math.min(maxPosition, newPosition));
        
        this.handle.style.left = newPosition + 'px';
        this.handle.style.transition = 'none';
        
        const progress = 1 - ((newPosition - 10) / (maxPosition - 10));
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
        const currentPosition = parseInt(this.handle.style.left) || trackWidth - handleWidth - 20;
        const maxPosition = trackWidth - handleWidth - 20;
        const threshold = maxPosition * 0.4;

        if (currentPosition < threshold) {
            this.activate();
        } else {
            this.deactivate();
        }
    }

    handleClick(e) {
        if (this.isDragging) return;
        
        const rect = this.track.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        
        if (clickX < rect.width / 2) {
            this.activate();
        } else {
            this.deactivate();
        }
    }

    activate() {
        this.isActive = true;
        this.track.classList.add('active');
        this.handle.style.left = '10px';
        this.updateTrackProgress(1);
        
        setTimeout(() => {
            window.location.href = this.targetPage;
        }, 500);
    }

    deactivate() {
        this.isActive = false;
        this.track.classList.remove('active');
        const trackWidth = this.track.offsetWidth;
        const handleWidth = this.handle.offsetWidth;
        this.handle.style.left = (trackWidth - handleWidth - 20) + 'px';
        this.updateTrackProgress(0);
    }

    updateTrackProgress(progress) {
        const percentage = progress * 100;
        this.track.style.setProperty('--progress', percentage + '%');
    }
}

// Initialize only reverse slider
document.addEventListener('DOMContentLoaded', () => {
    const sliderContainer = document.querySelector('.slider-container');
    if (sliderContainer) {
        new ReverseSlider(sliderContainer, '/');
    }
});

