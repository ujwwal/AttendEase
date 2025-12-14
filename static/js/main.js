// AttendEase - Main JavaScript

document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateX(100px)';
            setTimeout(() => msg.remove(), 300);
        }, 5000);
    });

    // Animate progress bars on load
    const progressBars = document.querySelectorAll('.progress-bar .progress-fill');
    progressBars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0';
        setTimeout(() => {
            bar.style.width = width;
        }, 100);
    });

    // Animate stat values
    const statValues = document.querySelectorAll('.stat-value, .percentage-value, .card-value');
    statValues.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(10px)';
        setTimeout(() => {
            el.style.transition = 'all 0.5s ease';
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, 200);
    });

    // Subject card hover effects
    const subjectCards = document.querySelectorAll('.subject-card');
    subjectCards.forEach(card => {
        card.addEventListener('mouseenter', function () {
            this.style.transform = 'translateY(-4px)';
        });
        card.addEventListener('mouseleave', function () {
            this.style.transform = 'translateY(0)';
        });
    });
});

// API function for quick attendance toggle
async function toggleAttendance(subjectId, isPresent, date = null) {
    try {
        const response = await fetch('/api/toggle-attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                subject_id: subjectId,
                is_present: isPresent,
                date: date || new Date().toISOString().split('T')[0]
            })
        });

        if (!response.ok) {
            throw new Error('Failed to update attendance');
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error:', error);
        return null;
    }
}

// Confirm password match on registration
const confirmPasswordInput = document.getElementById('confirm_password');
const passwordInput = document.getElementById('password');

if (confirmPasswordInput && passwordInput) {
    confirmPasswordInput.addEventListener('input', function () {
        if (this.value !== passwordInput.value) {
            this.setCustomValidity('Passwords do not match');
        } else {
            this.setCustomValidity('');
        }
    });
}
