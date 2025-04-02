/**
 * EchoForge - Main JavaScript
 * 
 * This file handles the front-end interactions for the EchoForge application,
 * including voice listing, generation, playback, and theme switching.
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const voiceForm = document.getElementById('voice-form');
    const generateBtn = document.getElementById('generate-btn');
    const temperatureSlider = document.getElementById('temperature');
    const temperatureValue = document.getElementById('temperature-value');
    const topKSlider = document.getElementById('top_k');
    const topKValue = document.getElementById('top_k-value');
    const resultsSection = document.getElementById('results-section');
    const taskStatus = document.getElementById('task-status');
    const audioPlayer = document.getElementById('audio-player');
    const voiceAudio = document.getElementById('voice-audio');
    const downloadBtn = document.getElementById('download-btn');
    const copyLinkBtn = document.getElementById('copy-link-btn');
    const themeToggle = document.getElementById('theme-toggle');
    const themeToggleIcon = document.getElementById('theme-toggle-icon');
    const speakerSelect = document.getElementById('speaker_id');

    // Variables
    let currentTaskId = null;
    let statusCheckInterval = null;

    // Event Listeners - Add null checks to prevent errors
    if (voiceForm) voiceForm.addEventListener('submit', handleFormSubmit);
    if (temperatureSlider) temperatureSlider.addEventListener('input', updateTemperatureValue);
    if (topKSlider) topKSlider.addEventListener('input', updateTopKValue);
    if (downloadBtn) downloadBtn.addEventListener('click', downloadAudio);
    if (copyLinkBtn) copyLinkBtn.addEventListener('click', copyAudioLink);
    if (themeToggle) themeToggle.addEventListener('click', toggleTheme);

    // Initialize theme from localStorage
    initTheme();
    
    // Load available voices if on the generate page
    if (speakerSelect) {
        loadVoices();
    }
    
    // Load voices from API
    async function loadVoices() {
        try {
            // Try first with /api/voices/list endpoint
            let response = await fetch('/api/voices/list');
            
            // If that fails, try with /api/voices endpoint
            if (!response.ok && response.status === 404) {
                console.log('Trying alternate voice API endpoint...');
                response = await fetch('/api/voices');
            }
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const voices = await response.json();
            
            // Clear existing options except the placeholder
            while (speakerSelect.options.length > 1) {
                speakerSelect.remove(1);
            }
            
            // Add voice options
            if (Array.isArray(voices) && voices.length > 0) {
                voices.forEach(voice => {
                    if (!voice || typeof voice !== 'object') return;
                    
                    const option = document.createElement('option');
                    option.value = voice.speaker_id;
                    option.textContent = `${voice.name || 'Voice ' + voice.speaker_id} (${voice.gender || 'Unknown'})`;
                    speakerSelect.appendChild(option);
                });
            } else {
                console.warn('API returned empty or non-array voices data');
                addFallbackVoiceOptions();
            }
            
            // Enable the select
            speakerSelect.disabled = false;
        } catch (error) {
            console.error('Error loading voices:', error);
            // Add fallback options if voices can't be loaded
            addFallbackVoiceOptions();
        }
    }

    // Add fallback voice options
    function addFallbackVoiceOptions() {
        // Add some default voice options
        const defaultVoices = [
            { id: 1, name: "Default Male Voice", gender: "male" },
            { id: 2, name: "Default Female Voice", gender: "female" },
            { id: 3, name: "Deep Male Voice", gender: "male" },
            { id: 4, name: "Soft Female Voice", gender: "female" }
        ];
        
        defaultVoices.forEach(voice => {
            const option = document.createElement('option');
            option.value = voice.id;
            option.textContent = `${voice.name} (${voice.gender})`;
            speakerSelect.appendChild(option);
        });
    }

    // Theme functions
    function initTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        if (themeToggleIcon) {
            updateThemeIcon(savedTheme);
        }
    }

    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        if (themeToggleIcon) {
            updateThemeIcon(newTheme);
        }
    }

    function updateThemeIcon(theme) {
        if (themeToggleIcon) {
            themeToggleIcon.textContent = theme === 'light' ? '🌙' : '☀️';
        }
    }

    // Update slider values
    function updateTemperatureValue() {
        if (temperatureValue) {
            temperatureValue.textContent = temperatureSlider.value;
        }
    }

    function updateTopKValue() {
        if (topKValue) {
            topKValue.textContent = topKSlider.value;
        }
    }

    // Handle form submission
    async function handleFormSubmit(event) {
        event.preventDefault();
        
        // Disable the generate button
        if (generateBtn) {
            generateBtn.disabled = true;
            generateBtn.textContent = 'Generating...';
        }
        
        // Show results section with processing status
        if (resultsSection) resultsSection.style.display = 'block';
        if (taskStatus) taskStatus.textContent = 'Processing your request...';
        if (audioPlayer) audioPlayer.style.display = 'none';
        
        // Get form data
        const formData = new FormData(voiceForm);
        const data = {
            text: formData.get('text'),
            speaker_id: parseInt(formData.get('speaker_id')),
            temperature: parseFloat(formData.get('temperature')),
            top_k: parseInt(formData.get('top_k')),
            style: formData.get('style') || 'default',
            device: formData.get('device') || 'auto'
        };
        
        try {
            // Try the main API first
            let apiUrl = '/api/voices/generate';
            let response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            // If that fails with 404, try the v1 API
            if (!response.ok && response.status === 404) {
                console.log('Trying v1 API for generation...');
                apiUrl = '/api/v1/generate';
                response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
            }
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const result = await response.json();
            currentTaskId = result.task_id;
            
            if (!currentTaskId) {
                throw new Error('No task ID returned from server');
            }
            
            console.log('Generation task started with ID:', currentTaskId);
            
            // Start checking task status
            statusCheckInterval = setInterval(checkTaskStatus, 1000);
            
        } catch (error) {
            console.error('Error generating voice:', error);
            if (taskStatus) taskStatus.textContent = `Error: ${error.message}`;
            resetGenerateButton();
        }
    }
    
    // Check task status
    async function checkTaskStatus() {
        try {
            if (!currentTaskId) {
                console.error('No task ID available for status check');
                if (taskStatus) taskStatus.textContent = "Error: No task ID available";
                clearInterval(statusCheckInterval);
                resetGenerateButton();
                return;
            }

            // Use the appropriate API endpoint based on availability
            let taskUrl = `/api/voices/tasks/${currentTaskId}`;
            let response = await fetch(taskUrl);
            
            // Try v1 API if the main API fails
            if (!response.ok && response.status === 404) {
                console.log('Trying v1 API for task status...');
                taskUrl = `/api/v1/tasks/${currentTaskId}`;
                response = await fetch(taskUrl);
            }
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const taskData = await response.json();
            
            // Update status message
            if (taskStatus) taskStatus.textContent = `Status: ${taskData.status}`;
            
            // Check if task is complete
            if (taskData.status === 'completed') {
                clearInterval(statusCheckInterval);
                
                // Set audio source
                const fileUrl = taskData.file_url || taskData.result?.file_url || 
                                taskData.output_file || taskData.result?.output_file;
                                
                if (fileUrl && voiceAudio && audioPlayer) {
                    console.log('Setting audio URL:', fileUrl);
                    voiceAudio.src = fileUrl;
                    audioPlayer.style.display = 'block';
                    
                    // Set download and copy link data
                    if (downloadBtn) downloadBtn.dataset.url = fileUrl;
                    if (copyLinkBtn) copyLinkBtn.dataset.url = window.location.origin + fileUrl;
                    
                    if (taskStatus) taskStatus.textContent = 'Voice generation complete!';
                } else if (taskStatus) {
                    console.error('No file URL returned in completed task:', taskData);
                    taskStatus.textContent = 'Voice generated but no file URL was returned.';
                }
                
                resetGenerateButton();
                
            } else if (taskData.status === 'failed') {
                clearInterval(statusCheckInterval);
                if (taskStatus) taskStatus.textContent = `Generation failed: ${taskData.error || 'Unknown error'}`;
                resetGenerateButton();
            }
            
        } catch (error) {
            console.error('Error checking task status:', error);
            if (taskStatus) taskStatus.textContent = `Error checking status: ${error.message}`;
            clearInterval(statusCheckInterval);
            resetGenerateButton();
        }
    }
    
    // Reset generate button
    function resetGenerateButton() {
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Voice';
        }
    }
    
    // Download audio
    function downloadAudio() {
        if (!downloadBtn) return;
        
        const url = downloadBtn.dataset.url;
        if (url) {
            const link = document.createElement('a');
            link.href = url;
            link.download = 'echoforge_voice.wav';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }
    
    // Copy audio link
    function copyAudioLink() {
        if (!copyLinkBtn) return;
        
        const url = copyLinkBtn.dataset.url;
        if (url) {
            navigator.clipboard.writeText(url)
                .then(() => {
                    const originalText = copyLinkBtn.textContent;
                    copyLinkBtn.textContent = 'Copied!';
                    setTimeout(() => {
                        copyLinkBtn.textContent = originalText;
                    }, 2000);
                })
                .catch(err => {
                    console.error('Failed to copy link:', err);
                    alert('Failed to copy link to clipboard.');
                });
        }
    }

    // Range input value display
    document.querySelectorAll('input[type="range"]').forEach(range => {
        if (!range) return;
        
        const valueDisplay = range.parentElement?.querySelector('.parameter-value');
        if (valueDisplay) {
            // Update value display on input change
            range.addEventListener('input', () => {
                valueDisplay.textContent = range.value;
            });
            
            // Set initial value
            valueDisplay.textContent = range.value;
        }
    });
}); 