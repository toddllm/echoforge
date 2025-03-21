/**
 * EchoForge Admin Interface
 * Main JavaScript functionality for the admin interface
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all shared admin functionality
    initSidebar();
    initThemeToggle();
    initUserDropdown();
    initMessageDismissal();
    initModalControls();
    initTabNavigation();
    initSortableTables();
    initActionMenus();
    initPaginationControls();
    
    // Call page-specific initializers if the elements exist
    if (document.getElementById('model-scan-btn')) {
        initModelManagement();
    }
    
    if (document.getElementById('refresh-tasks-btn')) {
        initTaskManagement();
    }
    
    if (document.getElementById('refresh-logs-btn')) {
        initLogsViewer();
    }
    
    if (document.querySelector('.config-tabs')) {
        initConfigManagement();
    }
    
    if (document.querySelector('.voice-generation-section')) {
        initVoiceGeneration();
    }
});

/**
 * Sidebar functionality
 */
function initSidebar() {
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const adminContainer = document.querySelector('.admin-container');
    
    if (sidebarToggle && adminContainer) {
        sidebarToggle.addEventListener('click', function() {
            adminContainer.classList.toggle('sidebar-collapsed');
            
            // Store preference in localStorage
            const isCollapsed = adminContainer.classList.contains('sidebar-collapsed');
            localStorage.setItem('sidebar-collapsed', isCollapsed);
        });
        
        // Restore user preference on load
        const isCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
        if (isCollapsed) {
            adminContainer.classList.add('sidebar-collapsed');
        }
    }
}

/**
 * Theme toggle functionality
 */
function initThemeToggle() {
    const themeToggle = document.querySelector('.theme-toggle');
    const body = document.body;
    
    if (themeToggle && body) {
        themeToggle.addEventListener('click', function() {
            body.classList.toggle('dark-theme');
            
            // Save theme preference
            const theme = body.classList.contains('dark-theme') ? 'dark' : 'light';
            document.cookie = `theme=${theme}; path=/; max-age=${60*60*24*365}`;
            localStorage.setItem('theme', theme);
        });
        
        // Also check localStorage for theme preference
        const storedTheme = localStorage.getItem('theme');
        if (storedTheme === 'dark' && !body.classList.contains('dark-theme')) {
            body.classList.add('dark-theme');
        } else if (storedTheme === 'light' && body.classList.contains('dark-theme')) {
            body.classList.remove('dark-theme');
        }
    }
}

/**
 * User dropdown menu
 */
function initUserDropdown() {
    const userButton = document.querySelector('.user-button');
    const userDropdown = document.querySelector('.dropdown-menu');
    
    if (userButton && userDropdown) {
        userButton.addEventListener('click', function(event) {
            event.stopPropagation();
            userDropdown.classList.toggle('show');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(event) {
            if (userDropdown.classList.contains('show') && !event.target.closest('.user-menu')) {
                userDropdown.classList.remove('show');
            }
        });
    }
}

/**
 * Message dismissal
 */
function initMessageDismissal() {
    document.querySelectorAll('.message-close').forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.message').remove();
        });
    });
    
    // Auto-hide messages after 5 seconds
    setTimeout(function() {
        document.querySelectorAll('.message').forEach(message => {
            message.classList.add('fade-out');
            setTimeout(function() {
                if (message && message.parentNode) {
                    message.remove();
                }
            }, 500);
        });
    }, 5000);
}

/**
 * Modal controls
 */
function initModalControls() {
    // Close modal when clicking X or cancel button
    document.querySelectorAll('.close-modal, [id$="-cancel-btn"]').forEach(button => {
        if (button) {
            button.addEventListener('click', function() {
                const modal = this.closest('.modal');
                if (modal) {
                    modal.style.display = 'none';
                }
            });
        }
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    });
}

/**
 * Tab navigation
 */
function initTabNavigation() {
    const tabButtons = document.querySelectorAll('.tab-button');
    
    if (tabButtons.length > 0) {
        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Hide all tab contents
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                
                // Deactivate all tab buttons
                tabButtons.forEach(btn => {
                    btn.classList.remove('active');
                });
                
                // Activate clicked tab
                this.classList.add('active');
                const tabId = `${this.dataset.tab}-tab`;
                const tabContent = document.getElementById(tabId);
                if (tabContent) {
                    tabContent.classList.add('active');
                }
                
                // Store active tab in localStorage
                localStorage.setItem('active-admin-tab', this.dataset.tab);
            });
        });
        
        // Restore active tab from localStorage
        const activeTab = localStorage.getItem('active-admin-tab');
        if (activeTab) {
            const tabToActivate = document.querySelector(`.tab-button[data-tab="${activeTab}"]`);
            if (tabToActivate && !tabToActivate.classList.contains('active')) {
                tabToActivate.click();
            }
        }
    }
}

/**
 * Sortable tables
 */
function initSortableTables() {
    document.querySelectorAll('th.sortable').forEach(header => {
        header.addEventListener('click', function() {
            const table = this.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const sortField = this.dataset.sort;
            const sortIcon = this.querySelector('i');
            
            // Toggle sort direction
            const isAscending = sortIcon.classList.contains('fa-sort') || 
                               sortIcon.classList.contains('fa-sort-down');
            
            // Reset all sort icons
            table.querySelectorAll('th.sortable i').forEach(icon => {
                icon.className = 'fas fa-sort';
            });
            
            // Update sort icon
            sortIcon.className = isAscending ? 'fas fa-sort-up' : 'fas fa-sort-down';
            
            // Sort rows
            rows.sort((a, b) => {
                const aValue = a.querySelector(`td:nth-child(${Array.from(a.parentNode.children).indexOf(a) + 1})`).textContent.trim();
                const bValue = b.querySelector(`td:nth-child(${Array.from(b.parentNode.children).indexOf(b) + 1})`).textContent.trim();
                
                // Check if values are dates
                const aDate = new Date(aValue);
                const bDate = new Date(bValue);
                
                if (!isNaN(aDate) && !isNaN(bDate)) {
                    return isAscending ? aDate - bDate : bDate - aDate;
                }
                
                // Check if values are numbers
                const aNum = parseFloat(aValue);
                const bNum = parseFloat(bValue);
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return isAscending ? aNum - bNum : bNum - aNum;
                }
                
                // Default string comparison
                return isAscending ? 
                    aValue.localeCompare(bValue) : 
                    bValue.localeCompare(aValue);
            });
            
            // Remove existing rows
            rows.forEach(row => row.remove());
            
            // Add sorted rows
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

/**
 * Action menus
 */
function initActionMenus() {
    document.querySelectorAll('.action-button').forEach(button => {
        button.addEventListener('click', function(event) {
            event.stopPropagation();
            
            // Close all other dropdowns
            document.querySelectorAll('.action-dropdown').forEach(dropdown => {
                if (dropdown !== this.nextElementSibling) {
                    dropdown.classList.remove('show');
                }
            });
            
            // Toggle this dropdown
            const dropdown = this.nextElementSibling;
            if (dropdown && dropdown.classList.contains('action-dropdown')) {
                dropdown.classList.toggle('show');
            }
        });
    });
    
    // Close action dropdowns when clicking outside
    document.addEventListener('click', function() {
        document.querySelectorAll('.action-dropdown').forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    });
}

/**
 * Pagination controls
 */
function initPaginationControls() {
    document.querySelectorAll('.pagination-button, .pagination-page').forEach(button => {
        button.addEventListener('click', function() {
            if (!this.hasAttribute('disabled')) {
                // Handle pagination logic here
                // For now just log the action; this would be connected to backend via AJAX
                const page = this.dataset.page || this.textContent.trim();
                console.log(`Navigating to page: ${page}`);
                
                // Mock implementation: toggle active class
                if (this.classList.contains('pagination-page')) {
                    document.querySelectorAll('.pagination-page').forEach(btn => {
                        btn.classList.remove('active');
                    });
                    this.classList.add('active');
                }
            }
        });
    });
    
    // Page size selector
    const pageSizeSelect = document.getElementById('pagination-size-select');
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener('change', function() {
            // Handle page size change
            const pageSize = this.value;
            console.log(`Changed page size to: ${pageSize}`);
            // This would typically trigger a reload of the data with the new page size
        });
    }
}

/**
 * Model management functionality
 */
function initModelManagement() {
    // Scan for models button
    const scanBtn = document.getElementById('model-scan-btn');
    if (scanBtn) {
        scanBtn.addEventListener('click', function() {
            // Show a loading indication
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';
            this.disabled = true;
            
            // This would call an API endpoint to scan for models
            // For now, simulate with timeout
            setTimeout(() => {
                this.innerHTML = 'Scan for Models';
                this.disabled = false;
                showMessage('Models scan completed successfully.', 'success');
            }, 2000);
        });
    }
    
    // Model download button
    const downloadBtn = document.getElementById('model-download-btn');
    const downloadModal = document.getElementById('download-model-modal');
    
    if (downloadBtn && downloadModal) {
        downloadBtn.addEventListener('click', function() {
            downloadModal.style.display = 'block';
        });
    }
    
    // Connect details view buttons
    document.querySelectorAll('.view-model').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const modelId = this.dataset.modelId;
            const detailsModal = document.getElementById('model-details-modal');
            
            if (detailsModal) {
                // This would fetch model details from an API
                // Mock implementation for now
                document.getElementById('model-detail-name').textContent = `Model ${modelId}`;
                
                // Fetch direct CSM info
                fetchDirectCSMInfo();
                
                detailsModal.style.display = 'block';
            }
        });
    });
    
    // Direct CSM toggle button
    const toggleDirectCSMBtn = document.getElementById('toggle-direct-csm-btn');
    if (toggleDirectCSMBtn) {
        toggleDirectCSMBtn.addEventListener('click', function() {
            // Get current status
            const currentStatus = document.getElementById('direct-csm-enabled').textContent;
            const enable = currentStatus.toLowerCase() === 'false' || currentStatus.toLowerCase() === 'no';
            
            // Show loading state
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
            this.disabled = true;
            
            // Call API to toggle direct CSM
            fetch('/api/admin/models/toggle-direct-csm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ enable: enable })
            })
            .then(response => response.json())
            .then(data => {
                this.disabled = false;
                this.innerHTML = enable ? 'Disable Direct CSM' : 'Enable Direct CSM';
                
                if (data.status === 'success') {
                    showMessage(data.message, 'success');
                    // Update the UI
                    document.getElementById('direct-csm-enabled').textContent = data.direct_csm_enabled;
                    document.getElementById('direct-csm-status').textContent = data.direct_csm_enabled ? 'Active' : 'Inactive';
                    
                    // Update button text
                    this.innerHTML = data.direct_csm_enabled ? 'Disable Direct CSM' : 'Enable Direct CSM';
                } else {
                    showMessage(data.message, 'error');
                }
                
                // Refresh model info
                fetchDirectCSMInfo();
            })
            .catch(error => {
                this.disabled = false;
                this.innerHTML = enable ? 'Enable Direct CSM' : 'Disable Direct CSM';
                showMessage('Error toggling Direct CSM: ' + error, 'error');
            });
        });
    }
    
    // Test Direct CSM button
    const testDirectCSMBtn = document.getElementById('test-direct-csm-btn');
    if (testDirectCSMBtn) {
        testDirectCSMBtn.addEventListener('click', function() {
            // Show loading state
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
            this.disabled = true;
            
            // Call API to test direct CSM
            fetch('/api/admin/models/test-direct-csm', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                this.disabled = false;
                this.innerHTML = 'Test Direct CSM';
                
                if (data.status === 'error') {
                    showMessage(data.message, 'error');
                } else {
                    showMessage('Direct CSM test started. Task ID: ' + data.task_id, 'info');
                    
                    // Poll for task completion
                    pollTaskStatus(data.task_id);
                }
            })
            .catch(error => {
                this.disabled = false;
                this.innerHTML = 'Test Direct CSM';
                showMessage('Error testing Direct CSM: ' + error, 'error');
            });
        });
    }
}

/**
 * Fetch Direct CSM information
 */
function fetchDirectCSMInfo() {
    fetch('/api/admin/models/direct-csm-info')
        .then(response => response.json())
        .then(data => {
            // Update the UI
            document.getElementById('direct-csm-enabled').textContent = data.enabled;
            document.getElementById('direct-csm-path').textContent = data.path;
            document.getElementById('direct-csm-status').textContent = data.status;
            
            // Update toggle button text
            const toggleBtn = document.getElementById('toggle-direct-csm-btn');
            if (toggleBtn) {
                toggleBtn.innerHTML = data.enabled ? 'Disable Direct CSM' : 'Enable Direct CSM';
            }
            
            // Show warning if path doesn't exist or missing required files
            if (!data.path_exists) {
                showMessage('Warning: Direct CSM path does not exist. Please check the configuration.', 'warning');
            } else if (!data.has_required_files) {
                showMessage('Warning: Direct CSM path is missing required files. Please check the installation.', 'warning');
            }
        })
        .catch(error => {
            showMessage('Error fetching Direct CSM info: ' + error, 'error');
        });
}

/**
 * Poll task status
 */
function pollTaskStatus(taskId) {
    const pollInterval = setInterval(() => {
        fetch(`/api/admin/tasks/${taskId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'completed') {
                    clearInterval(pollInterval);
                    showMessage('Direct CSM test completed successfully!', 'success');
                    
                    // Show the audio file if available
                    if (data.result && data.result.file_url) {
                        const audioPlayer = document.createElement('audio');
                        audioPlayer.controls = true;
                        audioPlayer.src = data.result.file_url;
                        
                        const audioContainer = document.createElement('div');
                        audioContainer.className = 'audio-player-container';
                        audioContainer.innerHTML = '<h4>Test Audio</h4>';
                        audioContainer.appendChild(audioPlayer);
                        
                        // Add to the direct CSM section
                        const directCSMSection = document.getElementById('direct-csm-section');
                        if (directCSMSection) {
                            // Remove any existing audio player
                            const existingPlayer = directCSMSection.querySelector('.audio-player-container');
                            if (existingPlayer) {
                                existingPlayer.remove();
                            }
                            
                            directCSMSection.appendChild(audioContainer);
                        }
                    }
                } else if (data.status === 'failed') {
                    clearInterval(pollInterval);
                    showMessage('Direct CSM test failed: ' + (data.error || 'Unknown error'), 'error');
                }
                // Continue polling for 'pending' or 'processing' status
            })
            .catch(error => {
                clearInterval(pollInterval);
                showMessage('Error checking task status: ' + error, 'error');
            });
    }, 2000); // Poll every 2 seconds
}

/**
 * Task management functionality
 */
function initTaskManagement() {
    // Refresh tasks button
    const refreshBtn = document.getElementById('refresh-tasks-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            // Show a loading indication
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
            this.disabled = true;
            
            // This would call an API endpoint to refresh tasks
            // For now, simulate with timeout
            setTimeout(() => {
                this.innerHTML = 'Refresh Tasks';
                this.disabled = false;
                showMessage('Tasks refreshed successfully.', 'success');
            }, 1500);
        });
    }
    
    // Cleanup tasks button
    const cleanupBtn = document.getElementById('cleanup-tasks-btn');
    const cleanupModal = document.getElementById('cleanup-tasks-modal');
    
    if (cleanupBtn && cleanupModal) {
        cleanupBtn.addEventListener('click', function() {
            cleanupModal.style.display = 'block';
        });
    }
    
    // Task details view
    document.querySelectorAll('.view-task').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const taskId = this.dataset.taskId;
            const detailsModal = document.getElementById('task-details-modal');
            
            if (detailsModal) {
                // This would fetch task details from an API
                // Mock implementation for now
                document.getElementById('task-detail-id').textContent = taskId;
                detailsModal.style.display = 'block';
            }
        });
    });
}

/**
 * Logs viewer functionality
 */
function initLogsViewer() {
    // Refresh logs button
    const refreshBtn = document.getElementById('refresh-logs-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            // Show a loading indication
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
            this.disabled = true;
            
            // This would call an API endpoint to refresh logs
            // For now, simulate with timeout
            setTimeout(() => {
                this.innerHTML = 'Refresh Logs';
                this.disabled = false;
                showMessage('Logs refreshed successfully.', 'success');
            }, 1500);
        });
    }
    
    // Download logs button
    const downloadBtn = document.getElementById('download-logs-btn');
    const downloadModal = document.getElementById('download-modal');
    
    if (downloadBtn && downloadModal) {
        downloadBtn.addEventListener('click', function() {
            downloadModal.style.display = 'block';
        });
    }
    
    // Clear logs button
    const clearBtn = document.getElementById('clear-logs-btn');
    const clearModal = document.getElementById('clear-logs-modal');
    
    if (clearBtn && clearModal) {
        clearBtn.addEventListener('click', function() {
            clearModal.style.display = 'block';
        });
    }
    
    // Log filter controls
    const logFilterControls = document.querySelectorAll('#log-level-filter, #log-source-filter, #log-date-from, #log-date-to, #log-search');
    logFilterControls.forEach(control => {
        if (control) {
            control.addEventListener('change', applyLogFilters);
            
            if (control.type === 'text') {
                control.addEventListener('keyup', function(e) {
                    // Apply filter on Enter key
                    if (e.key === 'Enter') {
                        applyLogFilters();
                    }
                });
            }
        }
    });
    
    // Toggle traceback buttons
    document.querySelectorAll('.toggle-traceback').forEach(button => {
        button.addEventListener('click', function() {
            const traceback = this.nextElementSibling;
            const isVisible = traceback.style.display !== 'none';
            
            traceback.style.display = isVisible ? 'none' : 'block';
            this.textContent = isVisible ? '⊕' : '⊖';
            this.title = isVisible ? 'Show traceback' : 'Hide traceback';
        });
    });
}

/**
 * Apply log filters
 */
function applyLogFilters() {
    const level = document.getElementById('log-level-filter')?.value || 'all';
    const source = document.getElementById('log-source-filter')?.value || 'all';
    const dateFrom = document.getElementById('log-date-from')?.value;
    const dateTo = document.getElementById('log-date-to')?.value;
    const searchText = document.getElementById('log-search')?.value?.toLowerCase() || '';
    
    const logRows = document.querySelectorAll('.log-row');
    
    logRows.forEach(row => {
        let show = true;
        
        // Filter by level
        if (level !== 'all') {
            const rowLevel = row.querySelector('.log-level').textContent.toLowerCase();
            if (rowLevel !== level) {
                show = false;
            }
        }
        
        // Filter by source
        if (show && source !== 'all') {
            const rowSource = row.querySelector('.source-col').textContent;
            if (rowSource !== source) {
                show = false;
            }
        }
        
        // Filter by date range
        if (show && (dateFrom || dateTo)) {
            const rowDate = new Date(row.querySelector('.timestamp-col').textContent);
            
            if (dateFrom && new Date(dateFrom) > rowDate) {
                show = false;
            }
            
            if (dateTo && new Date(dateTo) < rowDate) {
                show = false;
            }
        }
        
        // Filter by search text
        if (show && searchText) {
            const rowMessage = row.querySelector('.message-col').textContent.toLowerCase();
            if (!rowMessage.includes(searchText)) {
                show = false;
            }
        }
        
        // Apply visibility
        row.style.display = show ? '' : 'none';
    });
    
    // Show "no logs" message if no visible logs
    const visibleLogCount = Array.from(logRows).filter(row => row.style.display !== 'none').length;
    const noLogsMessage = document.querySelector('.no-logs-message');
    
    if (noLogsMessage) {
        noLogsMessage.style.display = visibleLogCount === 0 ? 'block' : 'none';
    }
}

/**
 * Configuration management
 */
function initConfigManagement() {
    // Form submission for all config forms
    document.querySelectorAll('.config-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
                submitBtn.disabled = true;
                
                // This would send the form data to an API endpoint
                // For now, simulate with timeout
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                    showMessage('Configuration saved successfully.', 'success');
                    
                    // Check if restart is needed
                    const requiresRestart = Math.random() > 0.5; // For demo purposes
                    if (requiresRestart) {
                        const restartModal = document.getElementById('restart-modal');
                        if (restartModal) {
                            restartModal.style.display = 'block';
                        }
                    }
                }, 1500);
            }
        });
    });
    
    // Enable/disable auth fields based on checkbox
    const enableAuthCheckbox = document.getElementById('enable-auth');
    if (enableAuthCheckbox) {
        enableAuthCheckbox.addEventListener('change', function() {
            const authFields = document.querySelectorAll('#auth-username, #auth-password, #auth-required-public');
            authFields.forEach(field => {
                field.disabled = !this.checked;
            });
        });
    }
    
    // Enable/disable direct CSM path field based on checkbox
    const useDirectCSMCheckbox = document.getElementById('use-direct-csm');
    if (useDirectCSMCheckbox) {
        useDirectCSMCheckbox.addEventListener('change', function() {
            const directCSMPathField = document.getElementById('direct-csm-path');
            if (directCSMPathField) {
                directCSMPathField.disabled = !this.checked;
            }
        });
    }
    
    // Save all changes button
    const saveAllBtn = document.getElementById('save-all-btn');
    if (saveAllBtn) {
        saveAllBtn.addEventListener('click', function() {
            // Show loading state
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving All...';
            this.disabled = true;
            
            // This would submit all forms
            // For now, simulate with timeout
            setTimeout(() => {
                this.innerHTML = 'Save All Changes';
                this.disabled = false;
                showMessage('All configurations saved successfully.', 'success');
            }, 2000);
        });
    }
}

/**
 * Show a message notification
 * @param {string} text - Message text
 * @param {string} type - Message type (success, error, warning, info)
 */
function showMessage(text, type = 'info') {
    const messagesContainer = document.querySelector('.messages');
    if (!messagesContainer) return;
    
    const message = document.createElement('div');
    message.className = `message message-${type}`;
    
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'exclamation-circle';
    if (type === 'warning') icon = 'exclamation-triangle';
    
    message.innerHTML = `
        <div class="message-icon">
            <i class="fas fa-${icon}"></i>
        </div>
        <div class="message-content">
            ${text}
        </div>
        <button class="message-close">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    messagesContainer.appendChild(message);
    
    // Add close button functionality
    message.querySelector('.message-close').addEventListener('click', function() {
        message.remove();
    });
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (message.parentNode) {
            message.classList.add('fade-out');
            setTimeout(() => {
                if (message.parentNode) {
                    message.remove();
                }
            }, 500);
        }
    }, 5000);
}

/**
 * Voice Generation Interface
 */
function initVoiceGeneration() {
    console.log('Initializing voice generation interface');
    
    // Range slider value display
    const temperatureSlider = document.getElementById('temperature');
    const temperatureValue = document.getElementById('temperature-value');
    if (temperatureSlider && temperatureValue) {
        temperatureSlider.addEventListener('input', function() {
            temperatureValue.textContent = this.value;
        });
    }
    
    // Voice generation form submission
    const generationForm = document.getElementById('voice-generation-form');
    if (generationForm) {
        generationForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Get form values
            const text = document.getElementById('text-to-speak').value.trim();
            const speakerId = parseInt(document.getElementById('speaker-voice').value);
            const temperature = parseFloat(document.getElementById('temperature').value);
            
            // Validate form
            if (!text) {
                showGenerationError('Please enter text to convert to speech.');
                return;
            }
            
            // Show generation status
            showGenerationStatus('Starting voice generation...', 0);
            
            // Disable form submission while processing
            document.getElementById('generate-voice-btn').disabled = true;
            
            // Clear previous error or result display
            document.querySelector('.generation-error').style.display = 'none';
            document.querySelector('.generation-result').style.display = 'none';
            document.querySelector('.device-info').style.display = 'none';
            document.querySelector('.status-message').style.display = 'none';
            
            // Call the API to generate voice
            console.log(`Generating voice: speakerId=${speakerId}, temperature=${temperature}`);
            
            fetch('/api/admin/generate-voice', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    speaker_id: speakerId,
                    temperature: temperature,
                    top_k: 50,
                    device: 'cuda',
                    reload_model: false
                })
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.detail || 'Error starting voice generation');
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('Voice generation started:', data);
                
                if (data.task_id) {
                    showGenerationStatus('Voice generation started', 10);
                    pollGenerationStatus(data.task_id);
                } else {
                    showGenerationError('No task ID returned from server');
                    document.getElementById('generate-voice-btn').disabled = false;
                }
            })
            .catch(error => {
                console.error('Error starting voice generation:', error);
                showGenerationError(error.message);
                document.getElementById('generate-voice-btn').disabled = false;
            });
        });
    }
    
    function pollGenerationStatus(taskId) {
        console.log('Starting to poll task status for:', taskId);
        let pollCount = 0;
        const maxPolls = 30; // Maximum number of polls before giving up
        
        const pollInterval = setInterval(() => {
            pollCount++;
            
            // Only log every 5th poll to reduce noise
            const shouldLog = pollCount % 5 === 0;
            if (shouldLog) {
                console.log(`Poll #${pollCount} for task ${taskId}`);
            }
            
            // Give up after too many polls
            if (pollCount > maxPolls) {
                clearInterval(pollInterval);
                showGenerationError('Task is taking too long. Please check server logs.');
                document.getElementById('generate-voice-btn').disabled = false;
                return;
            }
            
            fetch(`/api/admin/tasks/${taskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ task_id: taskId })
            })
            .then(response => {
                if (!response.ok) {
                    clearInterval(pollInterval);
                    throw new Error('Error fetching task status');
                }
                return response.json();
            })
            .then(data => {
                if (shouldLog) {
                    console.log('Task status:', data);
                }
                
                // Update device info if available
                if (data.device_info) {
                    const deviceInfoElement = document.querySelector('.device-info');
                    deviceInfoElement.textContent = data.device_info;
                    deviceInfoElement.style.display = 'block';
                }
                
                // Update status message if available
                if (data.message) {
                    const statusMessageElement = document.querySelector('.status-message');
                    statusMessageElement.textContent = data.message;
                    statusMessageElement.style.display = 'block';
                }
                
                switch (data.status) {
                    case 'pending':
                        showGenerationStatus('Task pending...', 25);
                        break;
                    case 'processing':
                        showGenerationStatus(`Processing voice... ${data.progress ? Math.round(data.progress) + '%' : ''}`, data.progress || 50);
                        break;
                    case 'completed':
                        clearInterval(pollInterval);
                        showGenerationStatus('Voice generated successfully!', 100);
                        showGenerationResult(data.result);
                        document.getElementById('generate-voice-btn').disabled = false;
                        break;
                    case 'failed':
                        clearInterval(pollInterval);
                        showGenerationStatus('Voice generation failed', 100);
                        showGenerationError(data.error || 'Failed to generate voice');
                        document.getElementById('generate-voice-btn').disabled = false;
                        break;
                    default:
                        showGenerationStatus(`Unknown status: ${data.status}`, 50);
                }
            })
            .catch(error => {
                console.error('Error polling task status:', error);
                clearInterval(pollInterval);
                showGenerationError(error.message);
                document.getElementById('generate-voice-btn').disabled = false;
            });
        }, 5000); // Poll every 5 seconds
    }
    
    function showGenerationStatus(message, progress = 0) {
        const statusDiv = document.querySelector('.generation-status');
        const progressBar = document.querySelector('.progress-bar');
        const messageElement = document.querySelector('.generation-message');
        
        statusDiv.style.display = 'block';
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
        progressBar.textContent = `${progress}%`;
        messageElement.textContent = message;
        
        document.querySelector('.generation-error').style.display = 'none';
        document.querySelector('.generation-result').style.display = 'none';
    }
    
    function showGenerationResult(result) {
        if (!result || !result.file_url) {
            showGenerationError('Voice generation completed but no audio file was returned');
            return;
        }
        
        const resultDiv = document.querySelector('.generation-result');
        const audioPlayer = document.getElementById('audio-player');
        const downloadLink = document.getElementById('download-link');
        
        // Set audio source - Use the file_url from the result
        audioPlayer.src = result.file_url;
        
        // Set download link - Use the file_url and filename from the result
        downloadLink.href = result.file_url;
        
        // Extract filename from URL for the download attribute
        const filename = result.file_url.split('/').pop();
        downloadLink.download = filename;
        
        // Show result container
        resultDiv.style.display = 'block';
        
        // Hide status container
        document.querySelector('.generation-status').style.display = 'none';
        
        // Log success for debugging
        console.log("Audio generated successfully:", result);
    }
    
    function showGenerationError(errorMessage) {
        const errorDiv = document.querySelector('.generation-error');
        const errorMessageElement = document.getElementById('error-message');
        
        errorDiv.style.display = 'block';
        errorMessageElement.textContent = errorMessage;
        
        document.querySelector('.generation-status').style.display = 'none';
        document.querySelector('.generation-result').style.display = 'none';
        
        // Log error for debugging
        console.error("Voice generation error:", errorMessage);
    }
}

// Initialize voice generation if we're on the voices page
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.voice-generation-section')) {
        initVoiceGeneration();
    }
}); 