/**
 * Main JavaScript File
 * Handles common functionality across all pages
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApplication();
});

/**
 * Initialize the application
 */
function initializeApplication() {
    // Initialize components based on current page
    initializeFlashMessages();
    initializeFormValidations();
    initializeCharts();
    initializeTooltips();
    initializeMobileMenu();
    initializeTheme();
    
    // Add global event listeners
    setupGlobalEventListeners();
    
    console.log('NeuroFace Analyzer initialized');
}

/**
 * Initialize flash messages
 */
function initializeFlashMessages() {
    const flashMessages = document.getElementById('flashMessages');
    if (!flashMessages) return;
    
    // Auto-dismiss flash messages after 5 seconds
    setTimeout(function() {
        const messages = flashMessages.querySelectorAll('.flash-message');
        messages.forEach(function(message) {
            animateOut(message);
        });
    }, 5000);
    
    // Add close button to each message
    const messages = flashMessages.querySelectorAll('.flash-message');
    messages.forEach(function(message) {
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '<i class="fas fa-times"></i>';
        closeBtn.className = 'flash-close';
        closeBtn.style.cssText = `
            background: none;
            border: none;
            color: inherit;
            cursor: pointer;
            padding: 0;
            margin-left: auto;
            font-size: 1rem;
            opacity: 0.7;
            transition: opacity 0.2s;
        `;
        
        closeBtn.addEventListener('mouseenter', () => {
            closeBtn.style.opacity = '1';
        });
        
        closeBtn.addEventListener('mouseleave', () => {
            closeBtn.style.opacity = '0.7';
        });
        
        closeBtn.addEventListener('click', () => {
            animateOut(message);
        });
        
        message.style.display = 'flex';
        message.style.alignItems = 'center';
        message.style.gap = '0.75rem';
        message.appendChild(closeBtn);
    });
}

/**
 * Animate element out
 */
function animateOut(element) {
    element.style.animation = 'slideOut 0.3s ease forwards';
    setTimeout(function() {
        element.remove();
    }, 300);
}

/**
 * Initialize form validations
 */
function initializeFormValidations() {
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
        
        // Add real-time validation
        const inputs = form.querySelectorAll('input[required], select[required]');
        inputs.forEach(input => {
            input.addEventListener('blur', () => validateInput(input));
            input.addEventListener('input', () => clearError(input));
        });
    });
    
    // Password confirmation validation
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        const confirmInput = document.querySelector('input[name="confirm_password"]');
        if (confirmInput) {
            input.addEventListener('input', () => validatePasswordMatch(input, confirmInput));
            confirmInput.addEventListener('input', () => validatePasswordMatch(input, confirmInput));
        }
    });
}

/**
 * Validate form
 */
function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    inputs.forEach(input => {
        if (!validateInput(input)) {
            isValid = false;
        }
    });
    
    // Validate password match
    const password = form.querySelector('input[type="password"]');
    const confirmPassword = form.querySelector('input[name="confirm_password"]');
    
    if (password && confirmPassword && password.value !== confirmPassword.value) {
        showError(confirmPassword, 'Passwords do not match');
        isValid = false;
    }
    
    return isValid;
}

/**
 * Validate single input
 */
function validateInput(input) {
    const value = input.value.trim();
    let isValid = true;
    let errorMessage = '';
    
    // Check required fields
    if (input.required && !value) {
        errorMessage = 'This field is required';
        isValid = false;
    }
    
    // Check email format
    if (input.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            errorMessage = 'Please enter a valid email address';
            isValid = false;
        }
    }
    
    // Check password strength
    if (input.type === 'password' && value) {
        if (value.length < 8) {
            errorMessage = 'Password must be at least 8 characters long';
            isValid = false;
        }
    }
    
    // Check age range
    if (input.name === 'age' && value) {
        const age = parseInt(value);
        if (age < 1 || age > 120) {
            errorMessage = 'Please enter a valid age (1-120)';
            isValid = false;
        }
    }
    
    if (!isValid) {
        showError(input, errorMessage);
    } else {
        clearError(input);
    }
    
    return isValid;
}

/**
 * Validate password match
 */
function validatePasswordMatch(password, confirmPassword) {
    if (password.value && confirmPassword.value && password.value !== confirmPassword.value) {
        showError(confirmPassword, 'Passwords do not match');
        return false;
    } else {
        clearError(confirmPassword);
        return true;
    }
}

/**
 * Show error message for input
 */
function showError(input, message) {
    clearError(input);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'form-error';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        color: #ef4444;
        font-size: 0.875rem;
        margin-top: 0.25rem;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    `;
    
    errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    
    input.style.borderColor = '#ef4444';
    input.parentNode.appendChild(errorDiv);
}

/**
 * Clear error from input
 */
function clearError(input) {
    input.style.borderColor = '';
    
    const errorDiv = input.parentNode.querySelector('.form-error');
    if (errorDiv) {
        errorDiv.remove();
    }
}

/**
 * Initialize charts
 */
function initializeCharts() {
    // Expression chart
    const expressionChart = document.getElementById('expression-chart');
    if (expressionChart && typeof Chart !== 'undefined') {
        createExpressionChart(expressionChart);
    }
    
    // Blink rate chart
    const blinkChart = document.getElementById('blink-chart');
    if (blinkChart && typeof Chart !== 'undefined') {
        createBlinkChart(blinkChart);
    }
    
    // Health score chart
    const healthScore = document.getElementById('health-score');
    if (healthScore) {
        createHealthScoreChart(healthScore);
    }
}

/**
 * Create expression chart
 */
function createExpressionChart(chartElement) {
    try {
        const data = JSON.parse(chartElement.dataset.expressions || '{}');
        const ctx = chartElement.getContext('2d');
        
        const chart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: Object.keys(data).map(key => key.charAt(0).toUpperCase() + key.slice(1)),
                datasets: [{
                    label: 'Expression Intensity',
                    data: Object.values(data),
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(59, 130, 246, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(59, 130, 246, 1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        },
                        pointLabels: {
                            font: {
                                size: 12,
                                family: 'Inter, sans-serif'
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.raw}%`;
                            }
                        }
                    }
                }
            }
        });
        
        return chart;
    } catch (error) {
        console.error('Error creating expression chart:', error);
        return null;
    }
}

/**
 * Create blink rate chart
 */
function createBlinkChart(chartElement) {
    try {
        const blinkRate = parseFloat(chartElement.dataset.rate || '0');
        const ctx = chartElement.getContext('2d');
        
        // Determine color based on blink rate
        let color;
        if (blinkRate < 10) {
            color = '#ef4444'; // Red for low
        } else if (blinkRate <= 20) {
            color = '#10b981'; // Green for normal
        } else {
            color = '#f59e0b'; // Yellow for high
        }
        
        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [blinkRate, 30 - blinkRate],
                    backgroundColor: [color, '#e5e7eb'],
                    borderWidth: 0,
                    circumference: 270,
                    rotation: 225
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false
                    }
                }
            }
        });
        
        // Add text in center
        const centerText = {
            id: 'centerText',
            beforeDraw(chart) {
                const { ctx, chartArea: { width, height } } = chart;
                ctx.save();
                ctx.font = 'bold 24px Inter, sans-serif';
                ctx.fillStyle = color;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(`${blinkRate.toFixed(1)}/min`, width / 2, height / 2);
                
                ctx.font = '12px Inter, sans-serif';
                ctx.fillStyle = '#6b7280';
                ctx.fillText('blinks per minute', width / 2, height / 2 + 24);
                ctx.restore();
            }
        };
        
        chart.options.plugins.tooltip = centerText;
        chart.update();
        
        return chart;
    } catch (error) {
        console.error('Error creating blink chart:', error);
        return null;
    }
}

/**
 * Create health score chart
 */
function createHealthScoreChart(container) {
    const score = parseFloat(container.dataset.score || '0');
    
    // Determine color based on score
    let color;
    if (score < 60) {
        color = '#ef4444'; // Red for poor
    } else if (score < 80) {
        color = '#f59e0b'; // Yellow for fair
    } else {
        color = '#10b981'; // Green for good
    }
    
    // Update CSS variable for animation
    container.style.setProperty('--score', score / 100);
    container.style.setProperty('--score-color', color);
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

/**
 * Show tooltip
 */
function showTooltip(event) {
    const element = event.target;
    const tooltipText = element.getAttribute('data-tooltip');
    
    if (!tooltipText) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = tooltipText;
    tooltip.style.cssText = `
        position: absolute;
        background: #1f2937;
        color: white;
        padding: 0.5rem 0.75rem;
        border-radius: 0.375rem;
        font-size: 0.875rem;
        z-index: 1000;
        white-space: nowrap;
        pointer-events: none;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    `;
    
    document.body.appendChild(tooltip);
    
    // Position tooltip
    const rect = element.getBoundingClientRect();
    tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
    tooltip.style.left = `${rect.left + (rect.width - tooltip.offsetWidth) / 2}px`;
    
    // Store reference
    element._tooltip = tooltip;
}

/**
 * Hide tooltip
 */
function hideTooltip(event) {
    const element = event.target;
    if (element._tooltip) {
        element._tooltip.remove();
        delete element._tooltip;
    }
}

/**
 * Initialize mobile menu
 */
function initializeMobileMenu() {
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
            menuToggle.querySelector('i').classList.toggle('fa-bars');
            menuToggle.querySelector('i').classList.toggle('fa-times');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (event) => {
            if (!menuToggle.contains(event.target) && !mobileMenu.contains(event.target)) {
                mobileMenu.classList.add('hidden');
                menuToggle.querySelector('i').classList.remove('fa-times');
                menuToggle.querySelector('i').classList.add('fa-bars');
            }
        });
    }
}

/**
 * Initialize theme
 */
function initializeTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Check for saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    } else if (prefersDark) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
    
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
        updateThemeIcon(themeToggle);
    }
}

/**
 * Toggle theme
 */
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    updateThemeIcon(this);
}

/**
 * Update theme icon
 */
function updateThemeIcon(button) {
    const icon = button.querySelector('i');
    const currentTheme = document.documentElement.getAttribute('data-theme');
    
    if (currentTheme === 'dark') {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    } else {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
    }
}

/**
 * Setup global event listeners
 */
function setupGlobalEventListeners() {
    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // Print functionality
    const printButtons = document.querySelectorAll('[data-print]');
    printButtons.forEach(button => {
        button.addEventListener('click', () => window.print());
    });
    
    // Copy to clipboard
    const copyButtons = document.querySelectorAll('[data-copy]');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const text = this.getAttribute('data-copy');
            if (text) {
                navigator.clipboard.writeText(text).then(() => {
                    const originalText = this.innerHTML;
                    this.innerHTML = '<i class="fas fa-check"></i> Copied!';
                    setTimeout(() => {
                        this.innerHTML = originalText;
                    }, 2000);
                });
            }
        });
    });
}

/**
 * Utility function: Debounce
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Utility function: Format date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Utility function: Format time ago
 */
function timeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    let interval = Math.floor(seconds / 31536000);
    if (interval >= 1) {
        return interval + ' year' + (interval === 1 ? '' : 's') + ' ago';
    }
    
    interval = Math.floor(seconds / 2592000);
    if (interval >= 1) {
        return interval + ' month' + (interval === 1 ? '' : 's') + ' ago';
    }
    
    interval = Math.floor(seconds / 86400);
    if (interval >= 1) {
        return interval + ' day' + (interval === 1 ? '' : 's') + ' ago';
    }
    
    interval = Math.floor(seconds / 3600);
    if (interval >= 1) {
        return interval + ' hour' + (interval === 1 ? '' : 's') + ' ago';
    }
    
    interval = Math.floor(seconds / 60);
    if (interval >= 1) {
        return interval + ' minute' + (interval === 1 ? '' : 's') + ' ago';
    }
    
    return 'just now';
}

/**
 * Export functions for global use
 */
window.NeuroFace = {
    formatDate,
    timeAgo,
    debounce
};

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease forwards;
    }
    
    .hidden {
        display: none !important;
    }
    
    @media (max-width: 768px) {
        .mobile-hidden {
            display: none !important;
        }
        
        .mobile-block {
            display: block !important;
        }
    }
`;
document.head.appendChild(style);