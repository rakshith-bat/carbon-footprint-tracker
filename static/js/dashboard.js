document.addEventListener('DOMContentLoaded', () => {
    // Toggle Inputs for Renewables
    const triggers = document.querySelectorAll('.toggle-trigger');
    
    triggers.forEach(trigger => {
        trigger.addEventListener('change', (e) => {
            const targetId = e.target.dataset.target;
            const target = document.getElementById(targetId);
            if (target) {
                target.style.display = e.target.value === 'yes' ? 'block' : 'none';
                if (e.target.value === 'yes') {
                    target.focus();
                }
            }
        });
    });

    // Strict Hour Validation (Client-side)
    const hourInputs = document.querySelectorAll('.hour-input');
    
    hourInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            let val = parseFloat(e.target.value);
            
            if (val > 24) {
                e.target.value = 24;
                showWarning(e.target, "Max 24 hours allowed");
            } else if (val < 0) {
                e.target.value = 0;
            }
        });

        input.addEventListener('blur', (e) => {
            removeWarning(e.target);
        });
    });

    function showWarning(element, message) {
        // Check if warning already exists
        let parent = element.parentElement;
        let existing = parent.querySelector('.input-warning');
        if (!existing) {
            let warning = document.createElement('div');
            warning.className = 'input-warning';
            warning.innerText = message;
            warning.style.color = 'var(--accent-red)';
            warning.style.fontSize = '0.75rem';
            warning.style.marginTop = '4px';
            warning.style.fontFamily = 'JetBrains Mono';
            parent.appendChild(warning);
            
            // Glitch effect on warning
            warning.animate([
                { opacity: 0, transform: 'translateX(-5px)' },
                { opacity: 1, transform: 'translateX(0)' }
            ], { duration: 200 });
        }
    }

    function removeWarning(element) {
        let parent = element.parentElement;
        let existing = parent.querySelector('.input-warning');
        if (existing) {
            existing.remove();
        }
    }
});
