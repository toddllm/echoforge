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

    // Variables
    let currentTaskId = null;
    let statusCheckInterval = null;

    // Event Listeners
    voiceForm.addEventListener('submit', handleFormSubmit);
    temperatureSlider.addEventListener('input', updateTemperatureValue);
    topKSlider.addEventListener('input', updateTopKValue);
    downloadBtn.addEventListener('click', downloadAudio);
    copyLinkBtn.addEventListener('click', copyAudioLink);
    themeToggle.addEventListener('click', toggleTheme);

    // Initialize theme from localStorage
    initTheme();

    // Theme functions
    function initTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        updateThemeIcon(savedTheme);
    }

    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    }

    function updateThemeIcon(theme) {
        themeToggleIcon.textContent = theme === 'light' ? '🌙' : '☀️';
    }

    // Update slider values
    function updateTemperatureValue() {
        temperatureValue.textContent = temperatureSlider.value;
    }

    function updateTopKValue() {
        topKValue.textContent = topKSlider.value;
    }

    // Handle form submission
    async function handleFormSubmit(event) {
        event.preventDefault();
        
        // Disable the generate button
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';
        
        // Show results section with processing status
        resultsSection.style.display = 'block';
        taskStatus.textContent = 'Processing your request...';
        audioPlayer.style.display = 'none';
        
        // Get form data
        const formData = new FormData(voiceForm);
        const data = {
            text: formData.get('text'),
            speaker_id: parseInt(formData.get('speaker_id')),
            temperature: parseFloat(formData.get('temperature')),
            top_k: parseInt(formData.get('top_k')),
            style: formData.get('style')
        };
        
        try {
            // Send request to generate voice
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const result = await response.json();
            currentTaskId = result.task_id;
            
            // Start checking task status
            statusCheckInterval = setInterval(checkTaskStatus, 1000);
            
        } catch (error) {
            console.error('Error generating voice:', error);
            taskStatus.textContent = `Error: ${error.message}`;
            resetGenerateButton();
        }
    }
    
    // Check task status
    async function checkTaskStatus() {
        try {
            const response = await fetch(`/api/tasks/${currentTaskId}`);
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const taskData = await response.json();
            
            // Update status message
            taskStatus.textContent = `Status: ${taskData.status}`;
            
            // Check if task is complete
            if (taskData.status === 'completed') {
                clearInterval(statusCheckInterval);
                
                // Set audio source
                const fileUrl = taskData.file_url || taskData.result?.file_url;
                if (fileUrl) {
                    voiceAudio.src = fileUrl;
                    audioPlayer.style.display = 'block';
                    
                    // Set download and copy link data
                    downloadBtn.dataset.url = fileUrl;
                    copyLinkBtn.dataset.url = window.location.origin + fileUrl;
                    
                    taskStatus.textContent = 'Voice generation complete!';
                } else {
                    taskStatus.textContent = 'Voice generated but no file URL was returned.';
                }
                
                resetGenerateButton();
                
            } else if (taskData.status === 'failed') {
                clearInterval(statusCheckInterval);
                taskStatus.textContent = `Generation failed: ${taskData.error || 'Unknown error'}`;
                resetGenerateButton();
            }
            
        } catch (error) {
            console.error('Error checking task status:', error);
            taskStatus.textContent = `Error checking status: ${error.message}`;
            clearInterval(statusCheckInterval);
            resetGenerateButton();
        }
    }
    
    // Reset generate button
    function resetGenerateButton() {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Voice';
    }
    
    // Download audio
    function downloadAudio() {
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

    // Apply saved theme preference on page load
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
        if (themeToggleIcon) {
            themeToggleIcon.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
        }
    }
    
    // Range input value display
    document.querySelectorAll('input[type="range"]').forEach(range => {
        const valueDisplay = range.parentElement.querySelector('.parameter-value');
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