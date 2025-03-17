# CSM Voice Generation Scripts

This directory contains scripts for testing and using the CSM (Conversational Speech Model) for voice generation in the EchoForge project.

## Overview

The CSM model is a state-of-the-art text-to-speech model that generates natural-sounding voices. These scripts provide different ways to interact with the CSM model, from direct usage to integration with the EchoForge API.

## Scripts

### direct_csm_test.py

This script directly uses the CSM model to generate voice output, bypassing the EchoForge API layer. It's useful for testing the CSM model in isolation and diagnosing issues with voice generation.

**Usage:**
```bash
./scripts/direct_csm_test.py [text]
```

**Features:**
- Automatically finds the CSM model checkpoint
- Generates speech using the CSM model directly
- Saves the output to the EchoForge voices directory
- Creates a symlink for easy access to the latest generated file
- Works with the EchoForge voice browser

### test_csm_voice.py

This script uses the CSM adapter from the TTS POC to generate a voice file. It saves the output to the EchoForge generated directory so it will appear in the browser.

**Usage:**
```bash
./scripts/test_csm_voice.py [text]
```

### test_direct_csm.py

This script directly calls the CSM model in the movie_maker/voice_poc directory. It bypasses the adapter layer and directly uses the Generator class.

**Usage:**
```bash
./scripts/test_direct_csm.py [text]
```

### test_voice_api.py

This script tests the voice generation API endpoint directly. It sends a request to the running EchoForge server and saves the generated audio.

**Usage:**
```bash
./scripts/test_voice_api.py [text] [--server URL] [--port PORT] [--device cuda|cpu]
```

## Integration with EchoForge

The CSM model is integrated with EchoForge through the following components:

1. **Direct CSM Script**: For testing and development
2. **CSM Adapter**: Connects to the CSM model in the TTS POC
3. **Voice API**: Provides a REST API for generating voices
4. **Voice Browser**: Allows browsing and playing generated voices

## Troubleshooting

If you encounter issues with voice generation:

1. **Check the model checkpoint**: Ensure the CSM model checkpoint is correctly downloaded and accessible.
2. **Try direct generation**: Use the direct_csm_test.py script to bypass the API layer.
3. **Check device compatibility**: Try using CPU instead of GPU if CUDA issues occur.
4. **Examine the generated audio**: Use a tool like Audacity to examine the waveform.

## Future Improvements

- Integration with the admin page
- Support for different voices and styles
- Batch processing of voice generation
- Streaming audio output 