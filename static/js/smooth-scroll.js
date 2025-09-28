// Enhanced smooth scrolling functionality
document.addEventListener('DOMContentLoaded', function() {
    // Handle smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                // Custom smooth scroll with easing and highlight effect
                smoothScrollToElement(targetElement, 1200);
                
                // Add highlight effect for contact section
                if (targetId === 'contact') {
                    highlightContactSection();
                }
            }
        });
    });
    
    // Handle URL hash on page load (for direct links like about.html#contact)
    if (window.location.hash) {
        setTimeout(() => {
            const targetElement = document.querySelector(window.location.hash);
            if (targetElement) {
                smoothScrollToElement(targetElement, 1200);
                if (window.location.hash === '#contact') {
                    highlightContactSection();
                }
            }
        }, 100);
    }
});

// Custom smooth scroll function with enhanced easing
function smoothScrollToElement(element, duration = 1200) {
    const startPosition = window.pageYOffset;
    const targetPosition = element.getBoundingClientRect().top + window.pageYOffset - 60; // 60px offset for header
    const distance = targetPosition - startPosition;
    let startTime = null;
    
    // Enhanced easing function for ultra-smooth animation
    function easeInOutQuart(t) {
        return t < 0.5 ? 8 * t * t * t * t : 1 - 8 * (--t) * t * t * t;
    }
    
    function animation(currentTime) {
        if (startTime === null) startTime = currentTime;
        const timeElapsed = currentTime - startTime;
        const progress = Math.min(timeElapsed / duration, 1);
        
        const ease = easeInOutQuart(progress);
        const currentPosition = startPosition + (distance * ease);
        
        window.scrollTo(0, currentPosition);
        
        if (progress < 1) {
            requestAnimationFrame(animation);
        } else {
            // Ensure we end at exactly the right position
            window.scrollTo(0, targetPosition);
        }
    }
    
    requestAnimationFrame(animation);
}

// Add visual highlight effect when scrolling to contact section
function highlightContactSection() {
    const contactSection = document.getElementById('contact');
    if (contactSection) {
        // Add highlight class with delay to ensure scroll animation starts first
        setTimeout(() => {
            contactSection.classList.add('highlight-contact');
            
            // Remove highlight after animation
            setTimeout(() => {
                contactSection.classList.remove('highlight-contact');
            }, 2500);
        }, 200);
    }
}

// Enhanced intersection observer for smoother contact section detection
const contactObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting && entry.target.id === 'contact') {
            // Smooth fade-in effect when contact section comes into view
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'scale(1)';
        }
    });
}, {
    threshold: 0.2,
    rootMargin: '-50px 0px -50px 0px'
});

// Initialize observer when page loads
document.addEventListener('DOMContentLoaded', () => {
    const contactSection = document.getElementById('contact');
    if (contactSection) {
        contactObserver.observe(contactSection);
        
        // Set initial state for smooth entrance
        contactSection.style.transition = 'all 0.6s ease';
    }
});