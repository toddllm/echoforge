/**
 * EchoForge - Main JavaScript
 * This file contains client-side functionality for the EchoForge application.
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('EchoForge application initialized');
    
    // Initialize components
    initializeAudioPlayers();
    initializeGenerationForm();
    
    // Enable tooltips if any exist
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(initializeTooltip);
});

/**
 * Initialize audio players with custom controls
 */
function initializeAudioPlayers() {
    const audioPlayers = document.querySelectorAll('.audio-player');
    
    audioPlayers.forEach(player => {
        const audio = player.querySelector('audio');
        const playButton = player.querySelector('.play-button');
        const progressBar = player.querySelector('.progress-bar');
        const progressIndicator = player.querySelector('.progress-indicator');
        
        if (!audio || !playButton) return;
        
        // Play/pause functionality
        playButton.addEventListener('click', function() {
            if (audio.paused) {
                audio.play();
                playButton.classList.add('playing');
                playButton.innerHTML = '<span class="pause-icon">⏸</span>';
            } else {
                audio.pause();
                playButton.classList.remove('playing');
                playButton.innerHTML = '<span class="play-icon">▶</span>';
            }
        });
        
        // Update progress bar
        if (progressBar && progressIndicator) {
            audio.addEventListener('timeupdate', function() {
                const progress = (audio.currentTime / audio.duration) * 100;
                progressIndicator.style.width = `${progress}%`;
            });
            
            // Allow seeking
            progressBar.addEventListener('click', function(e) {
                const rect = progressBar.getBoundingClientRect();
                const pos = (e.clientX - rect.left) / rect.width;
                audio.currentTime = pos * audio.duration;
            });
        }
        
        // Reset play button when audio ends
        audio.addEventListener('ended', function() {
            playButton.classList.remove('playing');
            playButton.innerHTML = '<span class="play-icon">▶</span>';
        });
    });
}

/**
 * Initialize the speech generation form
 */
function initializeGenerationForm() {
    const generationForm = document.getElementById('generation-form');
    if (!generationForm) return;
    
    generationForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const text = document.getElementById('text-input').value.trim();
        const voice = document.getElementById('voice-select').value;
        const device = document.getElementById('device-select').value;
        
        if (!text) {
            showMessage('Please enter some text to generate.', 'error');
            return;
        }
        
        if (!voice) {
            showMessage('Please select a voice.', 'error');
            return;
        }
        
        // Show loading state
        showMessage('Generating speech...', 'info');
        setLoading(true);
        
        // Make API request
        fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                voice: voice,
                device: device
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.task_id) {
                checkTaskStatus(data.task_id);
            } else {
                throw new Error('No task ID received');
            }
        })
        .catch(error => {
            console.error('Error generating speech:', error);
            showMessage(`Error: ${error.message}`, 'error');
            setLoading(false);
        });
    });
}

/**
 * Check the status of a generation task
 */
function checkTaskStatus(taskId) {
    if (!taskId) return;
    
    const statusCheck = setInterval(() => {
        fetch(`/api/status/${taskId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                updateProgress(data.progress);
                
                if (data.status === 'complete') {
                    clearInterval(statusCheck);
                    showMessage('Speech generation complete!', 'success');
                    setLoading(false);
                    
                    if (data.output) {
                        displayGeneratedAudio(data.output);
                    }
                } else if (data.status === 'error') {
                    clearInterval(statusCheck);
                    showMessage(`Error: ${data.error}`, 'error');
                    setLoading(false);
                }
            })
            .catch(error => {
                console.error('Error checking task status:', error);
                // Don't clear interval on network errors, let it retry
            });
    }, 1000);
}

/**
 * Display generated audio
 */
function displayGeneratedAudio(audioPath) {
    const resultContainer = document.getElementById('result-container');
    if (!resultContainer) return;
    
    resultContainer.innerHTML = `
        <div class="panel">
            <h3 class="panel-title">Generated Speech</h3>
            <div class="audio-player">
                <audio src="/${audioPath}" preload="metadata"></audio>
                <div class="player-controls">
                    <button class="play-button"><span class="play-icon">▶</span></button>
                    <div class="progress-bar">
                        <div class="progress-indicator"></div>
                    </div>
                </div>
                <div class="player-info">
                    <a href="/${audioPath}" download class="download-link">Download Audio</a>
                </div>
            </div>
        </div>
    `;
    
    // Initialize the new audio player
    initializeAudioPlayers();
    
    // Show the result container
    resultContainer.style.display = 'block';
    
    // Scroll to result
    resultContainer.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Update progress indicator
 */
function updateProgress(progress) {
    const progressBar = document.getElementById('generation-progress');
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
    }
}

/**
 * Show a message to the user
 */
function showMessage(message, type = 'info') {
    const messageContainer = document.getElementById('message-container');
    if (!messageContainer) return;
    
    // Clear existing messages
    messageContainer.innerHTML = '';
    
    // Create message element
    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}-message`;
    messageElement.textContent = message;
    
    // Add dismiss button
    const dismissButton = document.createElement('button');
    dismissButton.className = 'dismiss-button';
    dismissButton.innerHTML = '&times;';
    dismissButton.addEventListener('click', () => {
        messageElement.remove();
    });
    
    messageElement.appendChild(dismissButton);
    messageContainer.appendChild(messageElement);
    
    // Auto-dismiss success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            messageElement.remove();
        }, 5000);
    }
}

/**
 * Set loading state
 */
function setLoading(isLoading) {
    const generateButton = document.querySelector('#generation-form button[type="submit"]');
    const progressContainer = document.getElementById('progress-container');
    
    if (generateButton) {
        generateButton.disabled = isLoading;
        generateButton.textContent = isLoading ? 'Generating...' : 'Generate Speech';
    }
    
    if (progressContainer) {
        progressContainer.style.display = isLoading ? 'block' : 'none';
    }
}

/**
 * Initialize a tooltip
 */
function initializeTooltip(element) {
    const tooltipText = element.getAttribute('data-tooltip');
    if (!tooltipText) return;
    
    // Create tooltip element
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = tooltipText;
    
    // Position tooltip on hover
    element.addEventListener('mouseenter', () => {
        document.body.appendChild(tooltip);
        
        const rect = element.getBoundingClientRect();
        tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
        tooltip.style.left = `${rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2)}px`;
        tooltip.style.opacity = '1';
    });
    
    element.addEventListener('mouseleave', () => {
        tooltip.style.opacity = '0';
        setTimeout(() => {
            if (tooltip.parentNode) {
                tooltip.parentNode.removeChild(tooltip);
            }
        }, 300);
    });
} 