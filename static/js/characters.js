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
        if (genderFilter) {
            genderFilter.addEventListener('change', updateCharacterGrid);
        }
        
        if (styleFilter) {
            styleFilter.addEventListener('change', updateCharacterGrid);
        }
        
        if (searchFilter) {
            searchFilter.addEventListener('input', updateCharacterGrid);
        }
        
        // Modal close event
        if (closeModal) {
            closeModal.addEventListener('click', () => {
                if (modal) {
                    modal.classList.remove('active');
                }
                // Stop any playing audio
                if (modalVoiceAudio) {
                    modalVoiceAudio.pause();
                }
            });
        }
        
        // Modal temperature slider
        if (modalTemperature && modalTemperatureValue) {
            modalTemperature.addEventListener('input', () => {
                modalTemperatureValue.textContent = modalTemperature.value;
            });
        }
        
        // Modal top-k slider
        if (modalTopK && modalTopKValue) {
            modalTopK.addEventListener('input', () => {
                modalTopKValue.textContent = modalTopK.value;
            });
        }
        
        // Modal generate button
        if (modalGenerateBtn) {
            modalGenerateBtn.addEventListener('click', generateVoice);
        }
        
        // Copy link button
        if (modalCopyLinkBtn) {
            modalCopyLinkBtn.addEventListener('click', () => {
                const url = modalCopyLinkBtn.dataset.url;
                if (url) {
                    navigator.clipboard.writeText(url)
                        .then(() => {
                            modalCopyLinkBtn.textContent = 'Copied!';
                            setTimeout(() => {
                                modalCopyLinkBtn.textContent = 'Copy Link';
                            }, 2000);
                        })
                        .catch(err => {
                            console.error('Error copying text: ', err);
                        });
                }
            });
        }
    }

    /**
     * Update the character grid based on filters
     */
    function updateCharacterGrid() {
        if (!characterGrid || !characters.length) return;
        
        // Get filter values
        const genderValue = genderFilter ? genderFilter.value : 'all';
        const styleValue = styleFilter ? styleFilter.value : 'all';
        const searchValue = searchFilter ? searchFilter.value.toLowerCase() : '';
        
        // Filter characters
        const filteredCharacters = characters.filter(character => {
            // Gender filter
            if (genderValue !== 'all' && character.gender !== genderValue) {
                return false;
            }
            
            // Style filter
            if (styleValue !== 'all' && character.style !== styleValue) {
                return false;
            }
            
            // Search filter
            if (searchValue && !character.name.toLowerCase().includes(searchValue)) {
                return false;
            }
            
            return true;
        });
        
        // Clear the grid
        characterGrid.innerHTML = '';
        
        // Show no results message if needed
        if (filteredCharacters.length === 0) {
            characterGrid.innerHTML = '<div class="no-results">No characters found matching your criteria.</div>';
            return;
        }
        
        // Add character cards
        filteredCharacters.forEach(character => {
            const card = createCharacterCard(character);
            if (card) {
                characterGrid.appendChild(card);
            }
        });
    }

    /**
     * Create a character card element
     */
    function createCharacterCard(character) {
        if (!cardTemplate) return null;
        
        // Clone the template
        const card = cardTemplate.content.cloneNode(true);
        
        // Set card data
        const nameElement = card.querySelector('.character-name');
        const genderBadge = card.querySelector('.gender-badge');
        const styleBadge = card.querySelector('.style-badge');
        const avatar = card.querySelector('.character-avatar');
        const playButton = card.querySelector('.play-sample');
        const detailsButton = card.querySelector('.view-details');
        
        if (nameElement) {
            nameElement.textContent = character.name;
        }
        
        if (genderBadge) {
            genderBadge.textContent = character.gender;
            genderBadge.classList.add(`gender-${character.gender.toLowerCase()}`);
        }
        
        if (styleBadge) {
            styleBadge.textContent = character.style;
            styleBadge.classList.add(`style-${character.style.toLowerCase()}`);
        }
        
        if (avatar) {
            avatar.src = character.image_url;
            avatar.alt = `${character.name} avatar`;
        }
        
        // Play button event
        if (playButton && character.sample_url) {
            const audio = new Audio(character.sample_url);
            
            playButton.addEventListener('click', (e) => {
                e.stopPropagation();
                
                // Toggle play/pause
                if (audio.paused) {
                    // Stop any other playing audio
                    document.querySelectorAll('.play-sample').forEach(btn => {
                        btn.classList.remove('playing');
                    });
                    
                    audio.play();
                    playButton.classList.add('playing');
                    
                    // Reset button when audio ends
                    audio.onended = () => {
                        playButton.classList.remove('playing');
                    };
                } else {
                    audio.pause();
                    audio.currentTime = 0;
                    playButton.classList.remove('playing');
                }
            });
        }
        
        // Details button event
        if (detailsButton) {
            detailsButton.addEventListener('click', () => {
                openCharacterModal(character);
            });
        }
        
        // Make the entire card clickable
        const cardElement = card.querySelector('.character-card');
        if (cardElement) {
            cardElement.addEventListener('click', () => {
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
        
        // Set modal content
        if (modalCharacterName) {
            modalCharacterName.textContent = character.name;
        }
        
        if (modalCharacterAvatar) {
            modalCharacterAvatar.src = character.image_url;
            modalCharacterAvatar.alt = `${character.name} avatar`;
        }
        
        if (modalCharacterDescription) {
            modalCharacterDescription.textContent = character.description;
        }
        
        if (modalGenderBadge) {
            modalGenderBadge.textContent = character.gender;
            modalGenderBadge.className = 'badge gender-badge';
            modalGenderBadge.classList.add(`gender-${character.gender.toLowerCase()}`);
        }
        
        if (modalStyleBadge) {
            modalStyleBadge.textContent = character.style;
            modalStyleBadge.className = 'badge style-badge';
            modalStyleBadge.classList.add(`style-${character.style.toLowerCase()}`);
        }
        
        // Reset generation UI
        if (modalText) {
            modalText.value = 'Hello, my name is ' + character.name + '. It\'s nice to meet you!';
        }
        
        if (modalTaskStatus) {
            modalTaskStatus.textContent = '';
            modalTaskStatus.classList.remove('error');
        }
        
        if (modalAudioPlayer) {
            modalAudioPlayer.style.display = 'none';
        }
        
        if (modalVoiceAudio) {
            modalVoiceAudio.src = '';
        }
        
        if (modalResult) {
            modalResult.classList.remove('active');
        }
        
        if (modalGenerateBtn) {
            modalGenerateBtn.disabled = false;
            modalGenerateBtn.textContent = 'Generate Voice';
        }
        
        // Show the modal
        modal.classList.add('active');
    }

    /**
     * Generate a voice sample
     */
    async function generateVoice() {
        if (!currentSpeakerId || !modalText || !modalTaskStatus) return;
        
        const text = modalText.value.trim();
        
        if (!text) {
            modalTaskStatus.textContent = 'Please enter some text to generate';
            modalTaskStatus.classList.add('error');
            return;
        }
        
        // Disable the generate button
        if (modalGenerateBtn) {
            modalGenerateBtn.disabled = true;
            modalGenerateBtn.textContent = 'Generating...';
        }
        
        // Hide the audio player
        if (modalAudioPlayer) {
            modalAudioPlayer.style.display = 'none';
        }
        
        // Reset the result area
        if (modalResult) {
            modalResult.classList.remove('active');
        }
        
        // Update status
        modalTaskStatus.textContent = 'Initializing...';
        modalTaskStatus.classList.remove('error');
        
        try {
            // Prepare request data
            const temperature = modalTemperature ? parseFloat(modalTemperature.value) : 0.5;
            const topK = modalTopK ? parseInt(modalTopK.value) : 50;
            const style = modalStyle ? modalStyle.value : 'default';
            
            // Get the reference audio for the current speaker
            const referenceAudio = `/static/voices/speaker_${currentSpeakerId}_temp_${temperature}_topk_${topK}_${style}.wav`;
            
            // Create form data to send
            const formData = new FormData();
            formData.append('reference_audio', referenceAudio);
            formData.append('text', text);
            
            // Send the request
            const response = await fetch('/api/voice-cloning/generate-speech', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Generate speech response:', data);
            
            // Get the task ID from the response
            currentTaskId = data.task_id;
            
            if (!currentTaskId) {
                throw new Error('No task ID returned from the server');
            }
            
            // Update status
            modalTaskStatus.textContent = 'Processing...';
            
            // Start checking the task status
            startTaskCheck();
            
        } catch (error) {
            console.error('Error generating voice:', error);
            modalTaskStatus.textContent = `Error: ${error.message}`;
            modalTaskStatus.classList.add('error');
            
            // Re-enable the generate button
            if (modalGenerateBtn) {
                modalGenerateBtn.disabled = false;
                modalGenerateBtn.textContent = 'Try Again';
            }
        }
    }

    /**
     * Start checking task status
     */
    function startTaskCheck() {
        // Clear any existing interval
        clearTaskCheckInterval();
        
        // Start a new interval
        taskCheckInterval = setInterval(async () => {
            try {
                await checkTaskStatus();
            } catch (error) {
                console.error('Error checking task status:', error);
                
                // Update status
                if (modalTaskStatus) {
                    modalTaskStatus.textContent = `Error: ${error.message}`;
                    modalTaskStatus.classList.add('error');
                }
                
                // Clear the interval
                clearTaskCheckInterval();
                
                // Re-enable generate button
                if (modalGenerateBtn) {
                    modalGenerateBtn.disabled = false;
                    modalGenerateBtn.textContent = 'Try Again';
                }
            }
        }, 1000);
    }

    /**
     * Check task status
     */
    async function checkTaskStatus() {
        if (!currentTaskId) return;
        
        console.log(`Checking task status for task: ${currentTaskId}`);
        try {
            const response = await fetch(`/api/voice-cloning/status/${currentTaskId}`);
            
            if (!response.ok) {
                console.error(`HTTP error! Status: ${response.status}`);
                
                // Handle the case where the task is not found (might be already completed)
                if (response.status === 404) {
                    console.log('Task not found, it might have been cleaned up after completion');
                    
                    // Try constructing the audio URL directly using the task ID
                    const audioFile = `character_voice_${currentTaskId}.wav`;
                    const directResultUrl = `/voices/${audioFile}`;
                    console.log('Trying direct URL:', directResultUrl);
                    
                    // Test if the file exists by creating a test image request
                    const testRequest = new Image();
                    testRequest.onload = function() {
                        console.log(`File exists at ${directResultUrl}`);
                        completeTaskWithDirectUrl(directResultUrl, audioFile);
                    };
                    testRequest.onerror = function() {
                        console.error(`File does not exist at ${directResultUrl}`);
                        showTaskError('Task not found');
                    };
                    testRequest.src = directResultUrl;
                    
                    return; // Exit early, we're handling this case specially
                }
                
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Received task status data:', data);
            
            if (!modalTaskStatus) return;
            
            // Update status
            modalTaskStatus.textContent = data.status;
            
            // If task is complete
            if (data.status === 'completed') {
                clearTaskCheckInterval();
                
                // Check for result URL in different possible locations in the response
                let resultUrl = null;
                
                // Debug the response structure
                console.log('Task completed. Full response:', JSON.stringify(data));
                
                // Try different possible structures - with enhanced debugging
                console.log('Checking for audio URLs in data:', data);
                
                if (data.result_url && typeof data.result_url === 'string') {
                    resultUrl = data.result_url;
                    console.log('Found result_url directly in data:', resultUrl);
                } else if (data.result && data.result.result_url && typeof data.result.result_url === 'string') {
                    resultUrl = data.result.result_url;
                    console.log('Found result_url in data.result:', resultUrl);
                } else if (data.audio_file && typeof data.audio_file === 'string') {
                    // Construct URL from audio_file
                    resultUrl = `/voices/${data.audio_file}`;
                    console.log('Constructed URL from audio_file:', resultUrl);
                } else if (data.result && data.result.audio_file && typeof data.result.audio_file === 'string') {
                    // Construct URL from result.audio_file
                    resultUrl = `/voices/${data.result.audio_file}`;
                    console.log('Constructed URL from result.audio_file:', resultUrl);
                } else {
                    // Last resort fallback - construct URL from task_id if present
                    if (data.task_id && typeof data.task_id === 'string') {
                        resultUrl = `/voices/character_voice_${data.task_id}.wav`;
                        console.log('Constructed fallback URL from task_id:', resultUrl);
                    } else {
                        console.error('No usable audio information found in response');
                    }
                }
                
                // Show audio player
                if (modalAudioPlayer && modalVoiceAudio) {
                    modalAudioPlayer.style.display = 'block';
                    
                    if (!resultUrl) {
                        console.error('Error: Could not determine audio URL from the API response');
                        modalTaskStatus.textContent = 'Error: No audio URL provided';
                        modalTaskStatus.classList.add('error');
                    } else {
                        console.log('Setting audio source to:', resultUrl);
                        
                        // Validate URL before setting
                        if (resultUrl && resultUrl.startsWith('/voices/')) {
                            modalVoiceAudio.src = resultUrl;
                            modalVoiceAudio.load();
                            console.log('Audio source set and loading');
                        } else {
                            console.error('Invalid URL format:', resultUrl);
                            modalTaskStatus.textContent = 'Error: Invalid audio URL';
                            modalTaskStatus.classList.add('error');
                        }
                    }
                    
                    // Add handlers for audio loading
                    modalVoiceAudio.onerror = function() {
                        console.error('Error loading generated audio');
                        if (modalTaskStatus) {
                            modalTaskStatus.textContent = 'Error loading audio';
                            modalTaskStatus.classList.add('error');
                        }
                    };
                    
                    // Add success handler for audio loading
                    modalVoiceAudio.onloadeddata = function() {
                        console.log('✅ Audio loaded successfully:', modalVoiceAudio.src);
                        if (modalTaskStatus) {
                            modalTaskStatus.textContent = 'Audio loaded successfully';
                            modalTaskStatus.classList.add('success');
                        }
                    };
                    
                    // Set download link
                    if (modalDownloadBtn && resultUrl && resultUrl.startsWith('/voices/')) {
                        modalDownloadBtn.href = resultUrl;
                        modalDownloadBtn.download = `echoforge_${currentSpeakerId || 'voice'}_${Date.now()}.wav`;
                    }
                    
                    // Set copy link data
                    if (modalCopyLinkBtn && resultUrl && resultUrl.startsWith('/voices/')) {
                        modalCopyLinkBtn.dataset.url = resultUrl;
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
        } catch (error) {
            console.error('Error checking task status:', error);
            showTaskError(error.message);
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
     * Function to handle task completion when using a direct URL
     */
    function completeTaskWithDirectUrl(resultUrl, audioFile) {
        clearTaskCheckInterval();
        console.log('Completing task with direct URL:', resultUrl);
        
        // Show audio player
        if (modalAudioPlayer && modalVoiceAudio) {
            modalAudioPlayer.style.display = 'block';
            modalVoiceAudio.src = resultUrl;
            modalVoiceAudio.load();
            
            // Set download link
            if (modalDownloadBtn) {
                modalDownloadBtn.href = resultUrl;
                modalDownloadBtn.download = `echoforge_${currentSpeakerId || 'voice'}_${Date.now()}.mp3`;
            }
            
            // Set copy link data
            if (modalCopyLinkBtn) {
                modalCopyLinkBtn.dataset.url = resultUrl;
            }
        }
        
        // Update status
        if (modalTaskStatus) {
            modalTaskStatus.textContent = 'completed';
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
    }

    /**
     * Show task error message
     */
    function showTaskError(message) {
        if (modalTaskStatus) {
            modalTaskStatus.textContent = `Error: ${message}`;
            modalTaskStatus.classList.add('error');
        }
        
        // Re-enable generate button
        if (modalGenerateBtn) {
            modalGenerateBtn.disabled = false;
            modalGenerateBtn.textContent = 'Try Again';
        }
        
        clearTaskCheckInterval();
    }

    /**
     * Copy URL to clipboard
     */
    if (modalCopyLinkBtn) {
        modalCopyLinkBtn.addEventListener('click', () => {
            const url = modalCopyLinkBtn.dataset.url;
            if (url) {
                navigator.clipboard.writeText(url)
                    .then(() => {
                        modalCopyLinkBtn.textContent = 'Copied!';
                        setTimeout(() => {
                            modalCopyLinkBtn.textContent = 'Copy Link';
                        }, 2000);
                    })
                    .catch(err => {
                        console.error('Error copying text: ', err);
                    });
            }
        });
    }
});
