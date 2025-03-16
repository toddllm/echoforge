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
            characterGrid.innerHTML = `<div class="error-message">Error loading characters: ${error.message}</div>`;
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
            characters.forEach(character => {
                // Generate placeholder image based on speaker ID
                const imageId = (character.speaker_id % 10) + 1;
                const gender = character.gender || 'neutral';
                character.image_url = `/static/images/${gender}${imageId}.jpg`;
                
                // Add sample audio URL (this would be real in production)
                character.sample_url = `/static/samples/voice_${character.speaker_id}_sample.mp3`;
                
                // Add default style if not present
                character.style = character.style || 'default';
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
        genderFilter.addEventListener('change', updateCharacterGrid);
        styleFilter.addEventListener('change', updateCharacterGrid);
        searchFilter.addEventListener('input', updateCharacterGrid);
        
        // Modal events
        closeModal.addEventListener('click', () => {
            modal.style.display = 'none';
            clearTaskCheckInterval();
        });
        
        window.addEventListener('click', (event) => {
            if (event.target === modal) {
                modal.style.display = 'none';
                clearTaskCheckInterval();
            }
        });
        
        // Range input value display
        modalTemperature.addEventListener('input', () => {
            modalTemperatureValue.textContent = modalTemperature.value;
        });
        
        modalTopK.addEventListener('input', () => {
            modalTopKValue.textContent = modalTopK.value;
        });
        
        // Generate button
        modalGenerateBtn.addEventListener('click', generateVoice);
    }

    /**
     * Update the character grid based on filters
     */
    function updateCharacterGrid() {
        const gender = genderFilter.value;
        const style = styleFilter.value;
        const searchTerm = searchFilter.value.toLowerCase();
        
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
            characterGrid.appendChild(card);
        });
    }

    /**
     * Create a character card element
     */
    function createCharacterCard(character) {
        // Clone the template
        const card = cardTemplate.content.cloneNode(true).querySelector('.character-card');
        
        // Set data attributes
        card.dataset.speakerId = character.speaker_id;
        card.dataset.gender = character.gender;
        card.dataset.style = character.style;
        
        // Set content
        const avatar = card.querySelector('.character-avatar img');
        avatar.src = character.image_url;
        avatar.alt = `${character.name} avatar`;
        
        card.querySelector('.character-name').textContent = character.name;
        card.querySelector('.character-description').textContent = character.description;
        
        const genderBadge = card.querySelector('.gender-badge');
        genderBadge.textContent = character.gender.charAt(0).toUpperCase() + character.gender.slice(1);
        
        const styleBadge = card.querySelector('.style-badge');
        styleBadge.textContent = character.style.charAt(0).toUpperCase() + character.style.slice(1);
        
        // Set up audio player
        const audio = card.querySelector('audio');
        audio.src = character.sample_url;
        
        // Add event listeners
        const playButton = card.querySelector('.play-sample-btn');
        playButton.addEventListener('click', () => {
            const audioPlayer = card.querySelector('.audio-player');
            
            if (audioPlayer.classList.contains('active')) {
                audioPlayer.classList.remove('active');
                audio.pause();
                audio.currentTime = 0;
            } else {
                // Hide all other audio players
                document.querySelectorAll('.audio-player.active').forEach(player => {
                    player.classList.remove('active');
                    player.querySelector('audio').pause();
                    player.querySelector('audio').currentTime = 0;
                });
                
                audioPlayer.classList.add('active');
                audio.play();
            }
        });
        
        const generateButton = card.querySelector('.generate-btn');
        generateButton.addEventListener('click', () => {
            openCharacterModal(character);
        });
        
        return card;
    }

    /**
     * Open the character modal
     */
    function openCharacterModal(character) {
        // Set current speaker ID
        currentSpeakerId = character.speaker_id;
        
        // Reset modal state
        modalResult.style.display = 'none';
        modalResult.classList.remove('active');
        modalAudioPlayer.style.display = 'none';
        modalText.value = '';
        
        // Set character details
        modalCharacterName.textContent = character.name;
        modalCharacterAvatar.src = character.image_url;
        modalCharacterAvatar.alt = `${character.name} avatar`;
        modalCharacterDescription.textContent = character.description;
        
        modalGenderBadge.textContent = character.gender.charAt(0).toUpperCase() + character.gender.slice(1);
        modalStyleBadge.textContent = character.style.charAt(0).toUpperCase() + character.style.slice(1);
        
        // Set default style
        modalStyle.value = character.style;
        
        // Show modal
        modal.style.display = 'block';
    }

    /**
     * Generate a voice sample
     */
    async function generateVoice() {
        // Validate input
        if (!modalText.value.trim()) {
            alert('Please enter some text to convert to speech');
            return;
        }
        
        try {
            // Show result section
            modalResult.style.display = 'block';
            modalResult.classList.add('active');
            modalTaskStatus.textContent = 'Processing...';
            modalAudioPlayer.style.display = 'none';
            
            // Disable generate button
            modalGenerateBtn.disabled = true;
            
            // Prepare request data
            const requestData = {
                text: modalText.value,
                speaker_id: currentSpeakerId,
                temperature: parseFloat(modalTemperature.value),
                top_k: parseInt(modalTopK.value),
                style: modalStyle.value
            };
            
            // Send request to API
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            currentTaskId = data.task_id;
            
            // Start checking task status
            startTaskStatusCheck();
            
        } catch (error) {
            console.error('Error generating voice:', error);
            modalTaskStatus.textContent = `Error: ${error.message}`;
            modalGenerateBtn.disabled = false;
        }
    }

    /**
     * Start checking task status
     */
    function startTaskStatusCheck() {
        // Clear any existing interval
        clearTaskCheckInterval();
        
        // Set up new interval
        taskCheckInterval = setInterval(checkTaskStatus, 1000);
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
     * Check task status
     */
    async function checkTaskStatus() {
        if (!currentTaskId) return;
        
        try {
            const response = await fetch(`/api/tasks/${currentTaskId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const task = await response.json();
            
            // Update status display
            modalTaskStatus.textContent = `Status: ${task.status}`;
            
            // Handle completed task
            if (task.status === 'completed') {
                clearTaskCheckInterval();
                modalGenerateBtn.disabled = false;
                
                // Set audio source
                modalVoiceAudio.src = task.result.file_url;
                
                // Show audio player
                modalAudioPlayer.style.display = 'block';
                
                // Set up download button
                modalDownloadBtn.onclick = () => {
                    const a = document.createElement('a');
                    a.href = task.result.file_url;
                    a.download = task.result.file_url.split('/').pop();
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                };
                
                // Set up copy link button
                modalCopyLinkBtn.onclick = () => {
                    const fullUrl = window.location.origin + task.result.file_url;
                    navigator.clipboard.writeText(fullUrl)
                        .then(() => {
                            alert('Link copied to clipboard!');
                        })
                        .catch(err => {
                            console.error('Could not copy text: ', err);
                        });
                };
            }
            
            // Handle error
            if (task.status === 'error') {
                clearTaskCheckInterval();
                modalTaskStatus.textContent = `Error: ${task.error}`;
                modalGenerateBtn.disabled = false;
            }
            
        } catch (error) {
            console.error('Error checking task status:', error);
            modalTaskStatus.textContent = `Error checking status: ${error.message}`;
            clearTaskCheckInterval();
            modalGenerateBtn.disabled = false;
        }
    }
}); 