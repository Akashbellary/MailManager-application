// Email Triage AI - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form validations
    initializeFormValidations();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize file upload handlers
    initializeFileUpload();
    
    // Initialize auto-refresh for certain pages
    initializeAutoRefresh();
    
    // Initialize keyboard shortcuts
    initializeKeyboardShortcuts();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form validations
 */
function initializeFormValidations() {
    // CSV upload validation
    const csvFileInput = document.getElementById('csvFile');
    if (csvFileInput) {
        csvFileInput.addEventListener('change', function() {
            validateCSVFile(this);
        });
    }
    
    // Search form validation
    const searchForms = document.querySelectorAll('form[action*="search"]');
    searchForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const queryInput = this.querySelector('input[name="q"]');
            if (queryInput && queryInput.value.trim().length < 2) {
                e.preventDefault();
                showAlert('Please enter at least 2 characters to search.', 'warning');
            }
        });
    });
}

/**
 * Validate CSV file
 */
function validateCSVFile(input) {
    const file = input.files[0];
    if (!file) return;
    
    const fileName = file.name.toLowerCase();
    const fileSize = file.size / 1024 / 1024; // MB
    
    // Check file extension
    if (!fileName.endsWith('.csv')) {
        input.value = '';
        showAlert('Please select a CSV file.', 'danger');
        return;
    }
    
    // Check file size (max 50MB)
    if (fileSize > 50) {
        input.value = '';
        showAlert('File size must be less than 50MB.', 'danger');
        return;
    }
    
    // Update form text with file info
    const formText = input.nextElementSibling;
    if (formText && formText.classList.contains('form-text')) {
        formText.innerHTML = `
            File selected: <strong>${file.name}</strong> (${fileSize.toFixed(2)} MB)<br>
            File must be in CSV format with required columns: sender, subject, body, sent_date
        `;
    }
}

/**
 * Initialize search functionality
 */
function initializeSearch() {
    // Auto-suggest for search
    const searchInputs = document.querySelectorAll('input[name="q"]');
    searchInputs.forEach(input => {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    // Could implement auto-suggest here
                    console.log('Search query:', query);
                }, 300);
            }
        });
    });
    
    // Search keyboard shortcut (Ctrl/Cmd + K)
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[name="q"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
    });
}

/**
 * Initialize file upload with drag and drop
 */
function initializeFileUpload() {
    const fileInput = document.getElementById('csvFile');
    if (!fileInput) return;
    
    const uploadForm = fileInput.closest('form');
    if (!uploadForm) return;
    
    // Drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadForm.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadForm.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadForm.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight(e) {
        uploadForm.classList.add('dragover');
    }
    
    function unhighlight(e) {
        uploadForm.classList.remove('dragover');
    }
    
    uploadForm.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            validateCSVFile(fileInput);
        }
    }
}

/**
 * Initialize auto-refresh for certain pages
 */
function initializeAutoRefresh() {
    const currentPath = window.location.pathname;
    
    // Auto-refresh approval queue every 30 seconds
    if (currentPath.includes('/approval') && currentPath.includes('pending')) {
        setInterval(() => {
            // Only refresh if no modals are open and no forms are active
            const activeModals = document.querySelectorAll('.modal.show');
            const activeElement = document.activeElement;
            
            if (activeModals.length === 0 && 
                (!activeElement || (activeElement.tagName !== 'BUTTON' && activeElement.tagName !== 'INPUT'))) {
                window.location.reload();
            }
        }, 30000);
    }
}

/**
 * Initialize keyboard shortcuts
 */
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Escape key to close modals
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            });
        }
        
        // Arrow keys for pagination
        if (e.key === 'ArrowLeft' && e.ctrlKey) {
            const prevLink = document.querySelector('.pagination .page-item:not(.disabled) .page-link[href*="page=' + (getCurrentPage() - 1) + '"]');
            if (prevLink) {
                window.location.href = prevLink.href;
            }
        }
        
        if (e.key === 'ArrowRight' && e.ctrlKey) {
            const nextLink = document.querySelector('.pagination .page-item:not(.disabled) .page-link[href*="page=' + (getCurrentPage() + 1) + '"]');
            if (nextLink) {
                window.location.href = nextLink.href;
            }
        }
    });
}

/**
 * Get current page number from URL
 */
function getCurrentPage() {
    const urlParams = new URLSearchParams(window.location.search);
    return parseInt(urlParams.get('page')) || 1;
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info', duration = 5000) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert.alert-auto');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show alert-auto`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Insert after navbar
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        navbar.insertAdjacentElement('afterend', alertDiv);
    } else {
        document.body.insertBefore(alertDiv, document.body.firstChild);
    }
    
    // Auto-dismiss after duration
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, duration);
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
        return 'Today';
    } else if (diffDays === 1) {
        return 'Yesterday';
    } else if (diffDays < 7) {
        return `${diffDays} days ago`;
    } else {
        return date.toLocaleDateString();
    }
}

/**
 * Truncate text with ellipsis
 */
function truncateText(text, maxLength = 100) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showAlert('Copied to clipboard!', 'success', 2000);
        }).catch(() => {
            showAlert('Failed to copy to clipboard.', 'danger', 3000);
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showAlert('Copied to clipboard!', 'success', 2000);
        } catch (err) {
            showAlert('Failed to copy to clipboard.', 'danger', 3000);
        }
        document.body.removeChild(textArea);
    }
}

/**
 * Debounce function to limit API calls
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
 * Loading state management
 */
function setLoading(element, loading = true) {
    if (loading) {
        element.classList.add('loading');
        element.disabled = true;
        
        // Add spinner to buttons
        if (element.tagName === 'BUTTON') {
            const originalText = element.innerHTML;
            element.setAttribute('data-original-text', originalText);
            element.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Loading...';
        }
    } else {
        element.classList.remove('loading');
        element.disabled = false;
        
        // Restore button text
        if (element.tagName === 'BUTTON' && element.hasAttribute('data-original-text')) {
            element.innerHTML = element.getAttribute('data-original-text');
            element.removeAttribute('data-original-text');
        }
    }
}

/**
 * Confirm action with custom message
 */
function confirmAction(message = 'Are you sure?', callback = null) {
    if (confirm(message) && callback) {
        callback();
    }
}

/**
 * Toggle element visibility
 */
function toggleVisibility(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = element.style.display === 'none' ? 'block' : 'none';
    }
}

/**
 * Smooth scroll to element
 */
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

// Export functions for global use
window.EmailTriageAI = {
    showAlert,
    formatDate,
    truncateText,
    escapeHtml,
    copyToClipboard,
    debounce,
    setLoading,
    confirmAction,
    toggleVisibility,
    scrollToElement
};
