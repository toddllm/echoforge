/**
 * EchoForge Audio URL Fix 
 * This script directly patches the audio URL handling in the character showcase
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Audio fix script loaded - ' + new Date().toISOString());
    
    // Function to handle audio URL construction
    function constructProperAudioUrl(data) {
        console.log('🔍 Processing API response:', data);
        
        if (!data) {
            console.error('❌ No data provided to constructProperAudioUrl');
            return null;
        }
        
        let resultUrl = null;
        
        // Try different URL construction methods
        if (data.result_url && typeof data.result_url === 'string') {
            resultUrl = data.result_url;
            console.log('✓ Using result_url from API:', resultUrl);
        } 
        else if (data.audio_file && typeof data.audio_file === 'string') {
            resultUrl = `/voices/${data.audio_file}`;
            console.log('✓ Constructed URL from audio_file:', resultUrl);
        }
        else if (data.task_id && typeof data.task_id === 'string') {
            resultUrl = `/voices/character_voice_${data.task_id}.wav`;
            console.log('✓ Fallback: constructed URL from task_id:', resultUrl);
        }
        
        if (resultUrl && !resultUrl.startsWith('/voices/')) {
            console.warn('⚠️ URL does not start with /voices/:', resultUrl);
        }
        
        return resultUrl;
    }
    
    // Direct override of the checkTaskStatus function
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
        return originalFetch(url, options).then(response => {
            // Only process responses from the voice cloning status endpoint
            if (typeof url === 'string' && url.includes('/api/voice-cloning/status/')) {
                const clonedResponse = response.clone();
                
                // Process JSON responses
                if (response.headers.get('content-type')?.includes('application/json')) {
                    clonedResponse.json().then(data => {
                        console.log('📊 Status API Response:', data);
                        
                        // Ensure audio element gets the right URL when task is completed
                        if (data.status === 'completed') {
                            setTimeout(() => {
                                const audioElement = document.querySelector('#modal-voice-audio');
                                if (audioElement) {
                                    const properUrl = constructProperAudioUrl(data);
                                    if (properUrl && (!audioElement.src || audioElement.src === 'undefined')) {
                                        console.log('🔄 Fixing audio source. Old:', audioElement.src, 'New:', properUrl);
                                        audioElement.src = properUrl;
                                        audioElement.load();
                                        
                                        // Fix download button too
                                        const downloadBtn = document.querySelector('#modal-download-btn');
                                        if (downloadBtn) {
                                            downloadBtn.href = properUrl;
                                            downloadBtn.download = `echoforge_voice_${data.task_id}.wav`;
                                        }
                                        
                                        console.log('✅ Audio element fixed and loaded.');
                                    }
                                } else {
                                    console.warn('⚠️ Audio element not found in DOM');
                                }
                            }, 300); // Small delay to ensure DOM is updated
                        }
                    }).catch(e => console.error('Error parsing JSON:', e));
                }
            }
            return response;
        });
    };
    
    // Monitor for modal opening and audio loading
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                const modal = document.getElementById('character-modal');
                if (modal && getComputedStyle(modal).display !== 'none') {
                    console.log('🔔 Character modal opened - monitoring audio element');
                    
                    // Check for audio element
                    const audioElement = document.querySelector('#modal-voice-audio');
                    if (audioElement) {
                        // Add event listeners
                        audioElement.addEventListener('error', function(e) {
                            console.error('❌ Audio error:', e.target.error);
                            
                            // Try to recover if possible
                            const taskIdMatch = audioElement.src.match(/character_voice_([a-f0-9-]+)\.wav/);
                            if (taskIdMatch && taskIdMatch[1]) {
                                const taskId = taskIdMatch[1];
                                const fallbackUrl = `/voices/character_voice_${taskId}.wav`;
                                
                                if (audioElement.src !== fallbackUrl) {
                                    console.log('🔄 Trying fallback URL:', fallbackUrl);
                                    audioElement.src = fallbackUrl;
                                    audioElement.load();
                                }
                            }
                        });
                        
                        audioElement.addEventListener('loadeddata', function() {
                            console.log('✅ Audio loaded successfully:', audioElement.src);
                        });
                    }
                }
            }
        });
    });
    
    // Start observing
    observer.observe(document.body, { attributes: true, subtree: true });
    
    console.log('🔧 Audio fix script initialization complete');
});
