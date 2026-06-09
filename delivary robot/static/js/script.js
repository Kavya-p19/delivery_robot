// Add smooth scrolling for anchor links
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Add loading animation for order buttons
    const orderButtons = document.querySelectorAll('a[href*="order_product"]');
    orderButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!this.classList.contains('disabled')) {
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Ordering...';
                this.classList.add('disabled');
            }
        });
    });
});

// Add to existing JavaScript

// PIN input auto-formatting
document.addEventListener('DOMContentLoaded', function() {
    const pinInput = document.getElementById('pin_code');
    if (pinInput) {
        pinInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '').slice(0,4);
        });
        
        pinInput.addEventListener('keypress', function(e) {
            if (!/[0-9]/.test(e.key)) {
                e.preventDefault();
            }
        });
    }

    // Auto-focus PIN input
    if (window.location.pathname === '/verify_pin') {
        setTimeout(() => {
            const pinInput = document.getElementById('pin_code');
            if (pinInput) pinInput.focus();
        }, 500);
    }
});