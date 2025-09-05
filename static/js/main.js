// Email Triage AI - Enhanced Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeTooltips();
    initializeFormValidations();
    initializeSearch();
    initializeFileUpload();
    initializeAutoRefresh();
    initializeKeyboardShortcuts();
    initializeFilterSystem();
    initializeProgressTracking();
    
    console.log('Email Triage AI initialized successfully');
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
    
    // General form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton && !submitButton.disabled) {
                setLoading(submitButton, true);
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
    const fileInfo = document.getElementById('fileInfo');
    const submitBtn = document.getElementById('submitBtn');
    
    // Check file extension
    if (!fileName.endsWith('.csv')) {
        input.value = '';
        showAlert('Please select a CSV file.', 'danger');
        if (fileInfo) {
            fileInfo.innerHTML = '<span class="text-danger">Please select a CSV file.</span>';
        }
        if (submitBtn) submitBtn.disabled = true;
        return;
    }
    
    // Check file size (max 100MB)
    if (fileSize > 100) {
        input.value = '';
        showAlert('File size must be less than 100MB.', 'danger');
        if (fileInfo) {
            fileInfo.innerHTML = '<span class="text-danger">File size must be less than 100MB.</span>';
        }
        if (submitBtn) submitBtn.disabled = true;
        return;
    }
    
    // Update form text with file info
    if (fileInfo) {
        fileInfo.innerHTML = `
            <span class="text-success">File selected: <strong>${file.name}</strong> (${fileSize.toFixed(2)} MB)</span><br>
            File must be in CSV format with required columns: sender, subject, body, sent_date
        `;
    }
    if (submitBtn) submitBtn.disabled = false;
}

/**
 * Initialize enhanced search functionality
 */
function initializeSearch() {
    // Search input enhancements
    const searchInputs = document.querySelectorAll('input[name="q"]');
    searchInputs.forEach(input => {
        let searchTimeout;
        
        // Add placeholder enhancement for natural language
        if (input.placeholder.includes('Search')) {
            input.placeholder = 'Search emails naturally... (e.g., "negative emails", "emails from alice")';
        }
        
        // Auto-suggest functionality
        input.addEventListener('input', debounce(function() {
            const query = this.value.trim();
            
            if (query.length >= 2) {
                // Show search suggestions
                showSearchSuggestions(this, query);
            } else {
                hideSearchSuggestions(this);
            }
        }, 300));
        
        // Handle enter key
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.form.submit();
            }
        });
        
        // Hide suggestions when clicking outside
        document.addEventListener('click', function(e) {
            if (!input.contains(e.target)) {
                hideSearchSuggestions(input);
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
 * Show search suggestions
 */
function showSearchSuggestions(input, query) {
    // Remove existing suggestions
    hideSearchSuggestions(input);
    
    // Create suggestions dropdown
    const suggestions = [
        'negative emails',
        'positive feedback',
        'high priority emails',
        'support tickets',
        'login issues',
        'order inquiries',
        'technical problems'
    ];
    
    // Filter suggestions based on query
    const filteredSuggestions = suggestions.filter(s => 
        s.toLowerCase().includes(query.toLowerCase())
    );
    
    if (filteredSuggestions.length > 0) {
        const dropdown = document.createElement('div');
        dropdown.className = 'search-suggestions position-absolute bg-white border rounded shadow-sm';
        dropdown.style.cssText = 'top: 100%; left: 0; right: 0; z-index: 1000; max-height: 200px; overflow-y: auto;';
        
        filteredSuggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'suggestion-item p-2 border-bottom cursor-pointer';
            item.style.cursor = 'pointer';
            item.textContent = suggestion;
            
            item.addEventListener('click', function() {
                input.value = suggestion;
                hideSearchSuggestions(input);
                input.form.submit();
            });
            
            item.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#f8f9fa';
            });
            
            item.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '';
            });
            
            dropdown.appendChild(item);
        });
        
        // Position dropdown
        const inputContainer = input.closest('.input-group') || input.parentElement;
        inputContainer.style.position = 'relative';
        inputContainer.appendChild(dropdown);
        
        // Store reference for cleanup
        input._suggestionsDropdown = dropdown;
    }
}

/**
 * Hide search suggestions
 */
function hideSearchSuggestions(input) {
    if (input._suggestionsDropdown) {
        input._suggestionsDropdown.remove();
        input._suggestionsDropdown = null;
    }
}

/**
 * Initialize enhanced file upload with drag and drop
 */
function initializeFileUpload() {
    const fileInput = document.getElementById('csvFile');
    if (!fileInput) return;
    
    const uploadForm = fileInput.closest('form');
    if (!uploadForm) return;
    
    // Drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadForm.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
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
        uploadForm.classList.add('drag-over');
        showAlert('Drop CSV file here to upload', 'info', 2000);
    }
    
    function unhighlight(e) {
        uploadForm.classList.remove('drag-over');
    }
    
    uploadForm.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            const file = files[0];
            if (file.name.toLowerCase().endsWith('.csv')) {
                fileInput.files = files;
                validateCSVFile(fileInput);
                showAlert('CSV file ready for upload!', 'success');
            } else {
                showAlert('Please drop a CSV file.', 'warning');
            }
        }
    }
}

/**
 * Initialize auto-refresh for certain pages
 */
function initializeAutoRefresh() {
    const currentPath = window.location.pathname;
    
    // Auto-refresh approval queue every 30 seconds
    if (currentPath.includes('/approval')) {
        setInterval(() => {
            // Only refresh if no modals are open and no forms are active
            const activeModals = document.querySelectorAll('.modal.show');
            const activeElement = document.activeElement;
            
            if (activeModals.length === 0 && 
                (!activeElement || (activeElement.tagName !== 'BUTTON' && activeElement.tagName !== 'INPUT' && activeElement.tagName !== 'TEXTAREA'))) {
                
                // Add a subtle indication of refresh
                const refreshIndicator = document.createElement('div');
                refreshIndicator.className = 'position-fixed top-0 end-0 p-2';
                refreshIndicator.innerHTML = '<small class="text-muted"><i class="fas fa-sync-alt fa-spin"></i> Refreshing...</small>';
                document.body.appendChild(refreshIndicator);
                
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        }, 30000);
    }
}

/**
 * Initialize enhanced filter system
 */
function initializeFilterSystem() {
    const filterSelects = document.querySelectorAll('select[multiple]');
    
    filterSelects.forEach(select => {
        // Add filter count display
        const updateFilterCount = () => {
            const selected = select.selectedOptions.length;
            const label = select.closest('.col-md-3')?.querySelector('.form-label');
            if (label) {
                const baseText = label.textContent.split(' (')[0];
                if (selected > 0) {
                    label.textContent = `${baseText} (${selected} selected)`;
                    label.classList.add('text-primary', 'fw-bold');
                } else {
                    label.textContent = baseText;
                    label.classList.remove('text-primary', 'fw-bold');
                }
            }
        };
        
        select.addEventListener('change', updateFilterCount);
        updateFilterCount(); // Initial count
        
        // Enhanced styling for selected options
        select.addEventListener('change', function() {
            Array.from(this.options).forEach(option => {
                if (option.selected) {
                    option.style.backgroundColor = '#0d6efd';
                    option.style.color = 'white';
                } else {
                    option.style.backgroundColor = '';
                    option.style.color = '';
                }
            });
        });
        
        // Trigger initial styling
        select.dispatchEvent(new Event('change'));
    });
    
    // Smart filter clearing
    const clearButtons = document.querySelectorAll('a[href*="email_list"]:not([href*="?"]), .btn[href*="email_list"]:not([href*="?"])');
    clearButtons.forEach(button => {
        if (button.textContent.includes('Clear')) {
            button.addEventListener('click', function() {
                showAlert('All filters cleared', 'info', 2000);
            });
        }
    });
}

/**
 * Initialize progress tracking for uploads
 */
function initializeProgressTracking() {
    // Check if we're on a progress page
    const progressBar = document.getElementById('progressBar');
    if (progressBar) {
        // Add pulse animation for active progress
        if (progressBar.classList.contains('progress-bar-animated')) {
            progressBar.closest('.progress').classList.add('pulse');
        }
        
        // Smooth progress updates
        const originalWidth = progressBar.style.width;
        progressBar.style.width = '0%';
        setTimeout(() => {
            progressBar.style.width = originalWidth;
        }, 100);
    }
}

/**
 * Initialize keyboard shortcuts
 */
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Escape key to close modals and suggestions
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            });
            
            // Hide search suggestions
            const searchInputs = document.querySelectorAll('input[name="q"]');
            searchInputs.forEach(input => hideSearchSuggestions(input));
        }
        
        // Arrow keys for pagination navigation
        if (e.ctrlKey && !e.shiftKey && !e.altKey) {
            if (e.key === 'ArrowLeft') {
                const prevLink = document.querySelector('.pagination .page-item:not(.disabled) .page-link[href*="page=' + (getCurrentPage() - 1) + '"]');
                if (prevLink) {
                    e.preventDefault();
                    window.location.href = prevLink.href;
                }
            }
            
            if (e.key === 'ArrowRight') {
                const nextLink = document.querySelector('.pagination .page-item:not(.disabled) .page-link[href*="page=' + (getCurrentPage() + 1) + '"]');
                if (nextLink) {
                    e.preventDefault();
                    window.location.href = nextLink.href;
                }
            }
        }
        
        // Quick navigation shortcuts
        if (e.altKey && !e.ctrlKey && !e.shiftKey) {
            switch(e.key) {
                case 'd':
                    e.preventDefault();
                    window.location.href = '/';
                    break;
                case 'e':
                    e.preventDefault();
                    window.location.href = '/emails';
                    break;
                case 'a':
                    e.preventDefault();
                    window.location.href = '/approval';
                    break;
                case 'u':
                    e.preventDefault();
                    window.location.href = '/emails/upload';
                    break;
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
 * Enhanced alert system
 */
function showAlert(message, type = 'info', duration = 5000) {
    // Remove existing auto alerts
    const existingAlerts = document.querySelectorAll('.alert.alert-auto');
    existingAlerts.forEach(alert => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    });
    
    // Create new alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show alert-auto`;
    alertDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px; opacity: 0; transition: opacity 0.3s ease;';
    
    const icons = {
        success: 'fas fa-check-circle',
        danger: 'fas fa-exclamation-triangle',
        warning: 'fas fa-exclamation-circle',
        info: 'fas fa-info-circle',
        primary: 'fas fa-bell'
    };
    
    alertDiv.innerHTML = `
        <i class="${icons[type] || icons.info} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Fade in
    setTimeout(() => {
        alertDiv.style.opacity = '1';
    }, 10);
    
    // Auto-dismiss after duration
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.style.opacity = '0';
            setTimeout(() => alertDiv.remove(), 300);
        }
    }, duration);
    
    return alertDiv;
}

/**
 * Enhanced loading state management
 */
function setLoading(element, loading = true) {
    if (loading) {
        element.classList.add('loading');
        element.disabled = true;
        
        // Add spinner to buttons
        if (element.tagName === 'BUTTON') {
            const originalHTML = element.innerHTML;
            element.setAttribute('data-original-html', originalHTML);
            
            const icon = element.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-spinner fa-spin me-2';
            } else {
                element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>' + element.textContent;
            }
        }
    } else {
        element.classList.remove('loading');
        element.disabled = false;
        
        // Restore button content
        if (element.tagName === 'BUTTON' && element.hasAttribute('data-original-html')) {
            element.innerHTML = element.getAttribute('data-original-html');
            element.removeAttribute('data-original-html');
        }
    }
}

/**
 * Enhanced debounce function
 */
function debounce(func, wait, immediate = false) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

/**
 * Copy text to clipboard with enhanced feedback
 */
function copyToClipboard(text, successMessage = 'Copied to clipboard!') {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showAlert(successMessage, 'success', 2000);
        }).catch(() => {
            showAlert('Failed to copy to clipboard.', 'danger', 3000);
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showAlert(successMessage, 'success', 2000);
        } catch (err) {
            showAlert('Failed to copy to clipboard.', 'danger', 3000);
        }
        document.body.removeChild(textArea);
    }
}

/**
 * Smooth scroll to element with offset
 */
function scrollToElement(elementId, offset = 80) {
    const element = document.getElementById(elementId);
    if (element) {
        const elementPosition = element.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - offset;
        
        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    }
}

/**
 * Format numbers for display
 */
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Enhanced date formatting
 */
function formatDate(dateString, includeTime = false) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
        return includeTime ? `Today at ${date.toLocaleTimeString()}` : 'Today';
    } else if (diffDays === 1) {
        return includeTime ? `Yesterday at ${date.toLocaleTimeString()}` : 'Yesterday';
    } else if (diffDays < 7) {
        return includeTime ? `${diffDays} days ago at ${date.toLocaleTimeString()}` : `${diffDays} days ago`;
    } else {
        return includeTime ? date.toLocaleString() : date.toLocaleDateString();
    }
}

/**
 * Truncate text with smart word boundaries
 */
function truncateText(text, maxLength = 100, suffix = '...') {
    if (!text || text.length <= maxLength) return text;
    
    const truncated = text.substring(0, maxLength);
    const lastSpace = truncated.lastIndexOf(' ');
    
    if (lastSpace > 0 && lastSpace > maxLength * 0.8) {
        return truncated.substring(0, lastSpace) + suffix;
    }
    
    return truncated + suffix;
}

/**
 * Enhanced confirm dialog
 */
function confirmAction(message = 'Are you sure?', callback = null, type = 'warning') {
    const icons = {
        warning: 'fas fa-exclamation-triangle text-warning',
        danger: 'fas fa-exclamation-circle text-danger',
        info: 'fas fa-info-circle text-info'
    };
    
    // Create custom modal for better UX
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">
                        <i class="${icons[type] || icons.warning} me-2"></i>
                        Confirm Action
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>${message}</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary confirm-btn">Confirm</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
    
    modal.querySelector('.confirm-btn').addEventListener('click', function() {
        modalInstance.hide();
        if (callback) callback();
    });
    
    modal.addEventListener('hidden.bs.modal', function() {
        modal.remove();
    });
    
    return false; // Prevent default form submission
}

// Export enhanced functions for global use
window.EmailTriageAI = {
    showAlert,
    formatDate,
    formatNumber,
    formatFileSize,
    truncateText,
    copyToClipboard,
    debounce,
    setLoading,
    confirmAction,
    scrollToElement,
    hideSearchSuggestions,
    showSearchSuggestions
};

// Add custom CSS animations
const style = document.createElement('style');
style.textContent = `
    .drag-over {
        background-color: rgba(13, 110, 253, 0.1) !important;
        border-color: #0d6efd !important;
        transform: scale(1.02);
        transition: all 0.3s ease;
    }
    
    .search-suggestions {
        animation: slideDown 0.2s ease-out;
    }
    
    @keyframes slideDown {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .suggestion-item:hover {
        background-color: #f8f9fa !important;
        cursor: pointer;
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
`;
document.head.appendChild(style);

console.log('Email Triage AI: Enhanced JavaScript loaded successfully');
