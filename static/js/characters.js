/**
 * EchoForge Character Showcase
 * 
 * This script handles the character showcase functionality, including:
 * - Loading and displaying character cards
 * - Filtering characters by gender, style, and search term
 * - Playing voice samples
 * - Opening character details modal
 * - Generating new voice samples
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const characterGrid = document.getElementById('character-grid');
    const cardTemplate = document.getElementById('character-card-template');
    const genderFilter = document.getElementById('gender-filter');
    const styleFilter = document.getElementById('style-filter');
    const searchFilter = document.getElementById('search-filter');
    const modal = document.getElementById('character-modal');
    const closeModal = document.querySelector('.close-modal');
    const modalCharacterName = document.getElementById('modal-character-name');
    const modalCharacterAvatar = document.getElementById('modal-character-avatar');
    const modalCharacterDescription = document.getElementById('modal-character-description');
    const modalGenderBadge = document.getElementById('modal-gender-badge');
    const modalStyleBadge = document.getElementById('modal-style-badge');
    const modalText = document.getElementById('modal-text');
    const modalTemperature = document.getElementById('modal-temperature');
    const modalTemperatureValue = document.getElementById('modal-temperature-value');
    const modalTopK = document.getElementById('modal-top-k');
    const modalTopKValue = document.getElementById('modal-top-k-value');
    const modalStyle = document.getElementById('modal-style');
    const modalGenerateBtn = document.getElementById('modal-generate-btn');
    const modalResult = document.getElementById('modal-result');
    const modalTaskStatus = document.getElementById('modal-task-status');
    const modalAudioPlayer = document.getElementById('modal-audio-player');
    const modalVoiceAudio = document.getElementById('modal-voice-audio');
    const modalDownloadBtn = document.getElementById('modal-download-btn');
    const modalCopyLinkBtn = document.getElementById('modal-copy-link-btn');

    // State
    let characters = [];
    let currentSpeakerId = null;
    let currentTaskId = null;
    let taskCheckInterval = null;

    // Initialize
    init();

    /**
     * Initialize the character showcase
     */
    async function init() {
        try {
            await loadCharacters();
            setupEventListeners();
            updateCharacterGrid();
        } catch (error) {
            console.error('Error initializing character showcase:', error);
            if (characterGrid) {
                characterGrid.innerHTML = `<div class="error-message">Error loading characters: ${error.message}</div>`;
            }
        }
    }

    /**
     * Load characters from the API
     */
    async function loadCharacters() {
        try {
            const response = await fetch('/api/voices');
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            characters = await response.json();
            
            // Add placeholder images and sample URLs
            characters.forEach((character, index) => {
                // Ensure required properties exist
                character.name = character.name || `Voice ${index + 1}`;
                character.description = character.description || 'No description available';
                character.gender = character.gender || 'neutral';
                character.style = character.style || 'default';
                character.speaker_id = character.speaker_id || (index + 1);
                
                // Generate placeholder image based on speaker ID
                // Use a safe number for the image ID (1-5)
                const imageId = (Math.abs(parseInt(character.speaker_id) % 5) || 1) + 1;
                character.image_url = `/static/images/${character.gender}${imageId}.jpg`;
                
                // Add sample audio URL (this would be real in production)
                character.sample_url = `/static/samples/voice_${character.speaker_id}_sample.mp3`;
            });
            
        } catch (error) {
            console.error('Error fetching characters:', error);
            throw error;
        }
    }

    /**
     * Set up event listeners
     */
    function setupEventListeners() {
        // Filter change events
        if (genderFilter) genderFilter.addEventListener('change', updateCharacterGrid);
        if (styleFilter) styleFilter.addEventListener('change', updateCharacterGrid);
        if (searchFilter) searchFilter.addEventListener('input', updateCharacterGrid);
        
        // Modal events
        if (closeModal) {
            closeModal.addEventListener('click', () => {
                if (modal) modal.style.display = 'none';
                clearTaskCheckInterval();
            });
        }
        
        if (window) {
            window.addEventListener('click', (event) => {
                if (event.target === modal) {
                    modal.style.display = 'none';
                    clearTaskCheckInterval();
                }
            });
        }
        
        // Range input value display
        if (modalTemperature && modalTemperatureValue) {
            modalTemperature.addEventListener('input', () => {
                modalTemperatureValue.textContent = modalTemperature.value;
            });
        }
        
        if (modalTopK && modalTopKValue) {
            modalTopK.addEventListener('input', () => {
                modalTopKValue.textContent = modalTopK.value;
            });
        }
        
        // Generate button
        if (modalGenerateBtn) {
            modalGenerateBtn.addEventListener('click', generateVoice);
        }
    }

    /**
     * Update the character grid based on filters
     */
    function updateCharacterGrid() {
        if (!characterGrid) return;
        
        const gender = genderFilter ? genderFilter.value : 'all';
        const style = styleFilter ? styleFilter.value : 'all';
        const searchTerm = searchFilter ? searchFilter.value.toLowerCase() : '';
        
        // Clear the grid except for the template
        characterGrid.innerHTML = '';
        
        // Filter characters
        const filteredCharacters = characters.filter(character => {
            // Gender filter
            if (gender !== 'all' && character.gender !== gender) {
                return false;
            }
            
            // Style filter
            if (style !== 'all' && character.style !== style) {
                return false;
            }
            
            // Search filter
            if (searchTerm && !character.name.toLowerCase().includes(searchTerm)) {
                return false;
            }
            
            return true;
        });
        
        // Show message if no characters match filters
        if (filteredCharacters.length === 0) {
            characterGrid.innerHTML = '<div class="no-results">No characters match your filters</div>';
            return;
        }
        
        // Create and append character cards
        filteredCharacters.forEach(character => {
            const card = createCharacterCard(character);
            if (card) characterGrid.appendChild(card);
        });
    }

    /**
     * Create a character card element
     */
    function createCharacterCard(character) {
        if (!cardTemplate) return null;
        
        // Clone the template
        const card = cardTemplate.content.cloneNode(true).querySelector('.character-card');
        if (!card) return null;
        
        // Set data attributes
        card.dataset.speakerId = character.speaker_id || '';
        card.dataset.gender = character.gender || 'neutral';
        card.dataset.style = character.style || 'default';
        
        // Set content
        const avatar = card.querySelector('.character-avatar img');
        if (avatar) {
            avatar.src = character.image_url || '/static/images/placeholder.jpg';
            avatar.alt = `${character.name || 'Character'} avatar`;
            
            // Add error handler for image loading
            avatar.onerror = function() {
                this.src = '/static/images/placeholder.jpg';
                this.onerror = null; // Prevent infinite loop
            };
        }
        
        const nameElement = card.querySelector('.character-name');
        if (nameElement) nameElement.textContent = character.name || 'Unnamed Character';
        
        const descElement = card.querySelector('.character-description');
        if (descElement) descElement.textContent = character.description || 'No description available';
        
        const genderBadge = card.querySelector('.gender-badge');
        if (genderBadge) {
            const gender = character.gender || 'neutral';
            genderBadge.textContent = gender.charAt(0).toUpperCase() + gender.slice(1);
        }
        
        const styleBadge = card.querySelector('.style-badge');
        if (styleBadge) {
            const style = character.style || 'default';
            styleBadge.textContent = style.charAt(0).toUpperCase() + style.slice(1);
        }
        
        // Set up audio player
        const audio = card.querySelector('audio');
        if (audio) {
            audio.src = character.sample_url || '';
            
            // Add error handler for audio loading
            audio.onerror = function() {
                console.warn(`Failed to load audio sample for ${character.name}`);
                // Could set a default audio or disable the play button
            };
        }
        
        // Add event listeners
        const playButton = card.querySelector('.play-sample-btn');
        if (playButton && audio) {
            playButton.addEventListener('click', () => {
                const audioPlayer = card.querySelector('.audio-player');
                if (!audioPlayer) return;
                
                if (audioPlayer.classList.contains('active')) {
                    audioPlayer.classList.remove('active');
                    audio.pause();
                    audio.currentTime = 0;
                } else {
                    // Hide all other audio players
                    document.querySelectorAll('.audio-player.active').forEach(player => {
                        player.classList.remove('active');
                        const playerAudio = player.querySelector('audio');
                        if (playerAudio) {
                            playerAudio.pause();
                            playerAudio.currentTime = 0;
                        }
                    });
                    
                    audioPlayer.classList.add('active');
                    audio.play().catch(err => {
                        console.error('Error playing audio:', err);
                    });
                }
            });
        }
        
        const generateButton = card.querySelector('.generate-btn');
        if (generateButton) {
            generateButton.addEventListener('click', () => {
                openCharacterModal(character);
            });
        }
        
        return card;
    }

    /**
     * Open the character modal
     */
    function openCharacterModal(character) {
        if (!modal) return;
        
        // Set current speaker ID
        currentSpeakerId = character.speaker_id;
        
        // Reset modal state
        if (modalResult) {
            modalResult.style.display = 'none';
            modalResult.classList.remove('active');
        }
        if (modalAudioPlayer) modalAudioPlayer.style.display = 'none';
        if (modalText) modalText.value = '';
        
        // Set character details
        if (modalCharacterName) modalCharacterName.textContent = character.name || 'Unnamed Character';
        
        if (modalCharacterAvatar) {
            modalCharacterAvatar.src = character.image_url || '/static/images/placeholder.jpg';
            modalCharacterAvatar.alt = `${character.name || 'Character'} avatar`;
            
            // Add error handler for image loading
            modalCharacterAvatar.onerror = function() {
                this.src = '/static/images/placeholder.jpg';
                this.onerror = null; // Prevent infinite loop
            };
        }
        
        if (modalCharacterDescription) {
            modalCharacterDescription.textContent = character.description || 'No description available';
        }
        
        if (modalGenderBadge) {
            const gender = character.gender || 'neutral';
            modalGenderBadge.textContent = gender.charAt(0).toUpperCase() + gender.slice(1);
        }
        
        if (modalStyleBadge) {
            const style = character.style || 'default';
            modalStyleBadge.textContent = style.charAt(0).toUpperCase() + style.slice(1);
        }
        
        // Set default style
        if (modalStyle) modalStyle.value = character.style || 'default';
        
        // Show modal
        modal.style.display = 'block';
    }

    /**
     * Generate a voice sample
     */
    async function generateVoice() {
        if (!modalGenerateBtn || !modalText || !modalResult || !modalTaskStatus) return;
        
        const text = modalText.value.trim();
        if (!text) {
            alert('Please enter some text to generate');
            return;
        }
        
        // Get parameters
        const temperature = modalTemperature ? parseFloat(modalTemperature.value) : 0.7;
        const topK = modalTopK ? parseInt(modalTopK.value) : 50;
        const style = modalStyle ? modalStyle.value : 'default';
        
        // Disable generate button
        modalGenerateBtn.disabled = true;
        modalGenerateBtn.textContent = 'Generating...';
        
        // Show result section
        modalResult.style.display = 'block';
        modalTaskStatus.textContent = 'Initializing...';
        
        try {
            // Send request to API
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    speaker_id: currentSpeakerId || '1',
                    temperature: temperature,
                    top_k: topK,
                    style: style
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            currentTaskId = data.task_id;
            
            // Start checking task status
            modalTaskStatus.textContent = 'Processing...';
            startTaskCheck();
            
        } catch (error) {
            console.error('Error generating voice:', error);
            if (modalTaskStatus) {
                modalTaskStatus.textContent = `Error: ${error.message}`;
                modalTaskStatus.classList.add('error');
            }
            
            // Re-enable generate button
            if (modalGenerateBtn) {
                modalGenerateBtn.disabled = false;
                modalGenerateBtn.textContent = 'Generate';
            }
        }
    }

    /**
     * Start checking task status
     */
    function startTaskCheck() {
        clearTaskCheckInterval();
        
        taskCheckInterval = setInterval(async () => {
            try {
                await checkTaskStatus();
            } catch (error) {
                console.error('Error checking task status:', error);
                if (modalTaskStatus) {
                    modalTaskStatus.textContent = `Error: ${error.message}`;
                    modalTaskStatus.classList.add('error');
                }
                clearTaskCheckInterval();
                
                // Re-enable generate button
                if (modalGenerateBtn) {
                    modalGenerateBtn.disabled = false;
                    modalGenerateBtn.textContent = 'Generate';
                }
            }
        }, 2000);
    }

    /**
     * Check task status
     */
    async function checkTaskStatus() {
        if (!currentTaskId) return;
        
        const response = await fetch(`/api/tasks/${currentTaskId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!modalTaskStatus) return;
        
        // Update status
        modalTaskStatus.textContent = data.status;
        
        // If task is complete
        if (data.status === 'completed') {
            clearTaskCheckInterval();
            
            // Show audio player
            if (modalAudioPlayer && modalVoiceAudio) {
                modalAudioPlayer.style.display = 'block';
                modalVoiceAudio.src = data.result_url;
                modalVoiceAudio.load();
                
                // Add error handler for audio loading
                modalVoiceAudio.onerror = function() {
                    console.error('Error loading generated audio');
                    if (modalTaskStatus) {
                        modalTaskStatus.textContent = 'Error loading audio';
                        modalTaskStatus.classList.add('error');
                    }
                };
                
                // Set download link
                if (modalDownloadBtn && data.result_url) {
                    modalDownloadBtn.href = data.result_url;
                    modalDownloadBtn.download = `echoforge_${currentSpeakerId || 'voice'}_${Date.now()}.mp3`;
                }
                
                // Set copy link data
                if (modalCopyLinkBtn && data.result_url) {
                    modalCopyLinkBtn.dataset.url = data.result_url;
                }
            }
            
            // Add active class to result
            if (modalResult) {
                modalResult.classList.add('active');
            }
            
            // Re-enable generate button
            if (modalGenerateBtn) {
                modalGenerateBtn.disabled = false;
                modalGenerateBtn.textContent = 'Generate Again';
            }
        } else if (data.status === 'failed') {
            clearTaskCheckInterval();
            
            // Show error
            modalTaskStatus.textContent = `Failed: ${data.error || 'Unknown error'}`;
            modalTaskStatus.classList.add('error');
            
            // Re-enable generate button
            if (modalGenerateBtn) {
                modalGenerateBtn.disabled = false;
                modalGenerateBtn.textContent = 'Try Again';
            }
        }
    }

    /**
     * Clear task check interval
     */
    function clearTaskCheckInterval() {
        if (taskCheckInterval) {
            clearInterval(taskCheckInterval);
            taskCheckInterval = null;
        }
    }

    /**
     * Copy URL to clipboard
     */
    if (modalCopyLinkBtn) {
        modalCopyLinkBtn.addEventListener('click', () => {
            const url = modalCopyLinkBtn.dataset.url;
            if (!url) return;
            
            navigator.clipboard.writeText(url)
                .then(() => {
                    const originalText = modalCopyLinkBtn.textContent;
                    modalCopyLinkBtn.textContent = 'Copied!';
                    setTimeout(() => {
                        modalCopyLinkBtn.textContent = originalText;
                    }, 2000);
                })
                .catch(err => {
                    console.error('Failed to copy URL:', err);
                    alert('Failed to copy URL to clipboard');
                });
        });
    }
}); 