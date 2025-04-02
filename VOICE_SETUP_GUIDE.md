# EchoForge Voice Setup Guide

This guide provides detailed instructions for setting up voice files for the EchoForge voice generation system. It covers how to generate voice samples, where to place them, and how to use them in the system.

## Table of Contents

1. [Introduction](#introduction)
2. [Directory Structure](#directory-structure)
3. [Setting Up Voice Files](#setting-up-voice-files)
   - [Using the Setup Script](#using-the-setup-script)
   - [Manual Setup](#manual-setup)
4. [Voice Configuration](#voice-configuration)
5. [Testing Voice Files](#testing-voice-files)
6. [Troubleshooting](#troubleshooting)
7. [Custom Voice Creation](#custom-voice-creation)
8. [Advanced Configuration](#advanced-configuration)

## Introduction

EchoForge requires voice sample files to generate new speech. These sample files serve as reference points for the voice generation system. The `setup_voices.py` script automates the creation and placement of these files in the correct directory structure.

## Directory Structure

Voice files in EchoForge follow a specific directory structure:

```
echoforge/
├── static/
│   ├── voices/
│   │   ├── creative/       # Main directory for voice files
│   │   │   ├── voice_1_commander_sterling.wav
│   │   │   ├── voice_1_commander_sterling_variant1.wav
│   │   │   ├── voice_1_commander_sterling_variant2.wav
│   │   │   ├── voice_2_dr_elise_jensen.wav
│   │   │   └── ...
│   │   └── standard/       # Alternative voices (optional)
│   ├── samples/            # Audio samples for demonstrations
│   └── images/             # Speaker images
└── ...
```

Voice files must be placed in the `static/voices/creative` directory for the EchoForge system to find them.

## Setting Up Voice Files

### Using the Setup Script

The easiest way to set up voice files is to use the included `setup_voices.py` script:

1. Ensure you're in the EchoForge root directory:
   ```bash
   cd echoforge
   ```

2. Run the setup script:
   ```bash
   python setup_voices.py
   ```

3. The script will:
   - Create the necessary directory structure
   - Look for existing voice files in a movie_maker installation (if available)
   - Generate sample voice files with different characteristics
   - Create metadata and sample text files

If you want to regenerate voice files even if they already exist, use the `--force` flag:
```bash
python setup_voices.py --force
```

### Manual Setup

If you prefer to set up voice files manually:

1. Create the required directories:
   ```bash
   mkdir -p static/voices/creative
   mkdir -p static/samples
   mkdir -p static/images
   ```

2. Place compatible WAV files in the `static/voices/creative` directory, following this naming convention:
   ```
   voice_<speaker_id>_<voice_name>.wav
   ```
   
   Example: `voice_1_male_narrator.wav`

3. Ensure the WAV files are:
   - 16-bit mono audio
   - Sample rate of 22050Hz or higher
   - 3-5 seconds in duration
   - Clear speech with minimal background noise

## Voice Configuration

The default voice configuration includes five voices with different characteristics:

| ID | Name | Gender | Description |
|----|------|--------|-------------|
| 1 | Commander Sterling | Male | Deep authoritative voice with confident tone |
| 2 | Dr. Elise Jensen | Female | Clear, articulate voice with professional tone |
| 3 | James Fletcher | Male | Warm, friendly voice with natural cadence |
| 4 | Sophia Chen | Female | Energetic voice with varied intonation |
| 5 | Morgan Riley | Neutral | Balanced, neutral voice with moderate tone |

Each voice has associated parameters that define its characteristics:
- Base frequency (pitch)
- Formant shift (vocal tract characteristics)
- Duration
- Character traits

## Testing Voice Files

After setting up voice files, you can test them using the EchoForge debug page:

1. Start the EchoForge server:
   ```bash
   ./start_server.sh
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:8765/debug
   ```

3. In the debug interface:
   - Select a speaker ID (1-5) from the dropdown
   - Enter text to convert to speech
   - Click "Generate Voice"
   - Monitor the process in the debug logs
   - Play the resulting audio file

The debug page provides detailed information about the voice generation process, including:
- Request details
- Response data
- Task status updates
- Audio URL construction

## Troubleshooting

### Common Issues

1. **No voices appear in the dropdown**
   - Ensure voice files exist in `static/voices/creative`
   - Check file permissions (should be readable by the web server)
   - Verify file naming follows the pattern `voice_<id>_<name>.wav`

2. **Voice generation fails**
   - Check server logs for errors
   - Ensure the voice files are valid WAV files
   - Verify the sample rate and bit depth are compatible

3. **Generated voice sounds distorted**
   - The reference voice file may have poor quality
   - Try generating a new voice file with the setup script
   - Adjust temperature and top-k settings in the debug interface

4. **"Voice not found" error**
   - Ensure the speaker_id exists in your voice configuration
   - Check that the corresponding WAV file exists
   - Verify the file is readable by the server

### Checking Voice Files

You can inspect a voice file's properties using FFmpeg:

```bash
ffmpeg -i static/voices/creative/voice_1_commander_sterling.wav
```

The output should show details like sample rate, channels, and duration.

## Custom Voice Creation

You can create custom voices by:

1. Adding new entries to the `VOICE_CONFIGS` list in `setup_voices.py`
2. Running the script with the `--force` flag
3. Or manually creating compatible WAV files with your own voice recording setup

To create a custom voice manually:

1. Record a clear 3-5 second voice sample with minimal background noise
2. Convert it to the required format:
   ```bash
   ffmpeg -i your_recording.mp3 -ar 22050 -ac 1 -acodec pcm_s16le static/voices/creative/voice_6_custom_voice.wav
   ```

3. Test the voice using the debug page

## Advanced Configuration

### Modifying Voice Parameters

For more control over generated voices, you can modify these parameters in `setup_voices.py`:

- **base_freq**: The fundamental frequency of the voice (higher for female, lower for male)
- **formant_shift**: Controls vocal tract characteristics (>1.0 for smaller tracts, <1.0 for larger tracts)
- **duration**: Length of the voice sample in seconds
- **character_traits**: Descriptive tags for the voice

### Using the Debug Page for Development

The debug page is an invaluable tool for voice development:

1. Use the API version selector to test different endpoints
2. Observe detailed request and response information
3. Track task status changes in real-time
4. Validate audio URL construction
5. Test network connectivity to various endpoints

This helps identify and fix issues in the voice generation pipeline.

## Creating Your Own Voice Files

If you want to create your own custom voice files, you have several options:

### Option 1: Extending the setup script

The easiest approach is to modify the `setup_voices.py` script by adding your own voice configurations:

1. Open `setup_voices.py` in your editor
2. Find the `VOICE_CONFIGS` list at the top of the file
3. Add a new entry with your desired voice parameters:

```python
{
    "id": 6,  # Use a unique ID
    "name": "Your Voice Name",
    "gender": "male",  # or "female" or "neutral"
    "description": "Description of your voice",
    "base_freq": 120.0,  # Adjust frequency (lower for deeper voices)
    "formant_shift": 0.95,  # Adjust formant (affects voice quality)
    "duration": 4.0,  # Duration in seconds
    "character_traits": "your, voice, traits"
}
```

4. Run the script with the `--force` flag to regenerate all voices:
```bash
python setup_voices.py --force
```

### Option 2: Manual voice recording

For more realistic voices, you can record your own samples:

1. Record a clear voice sample (3-5 seconds) with minimal background noise
2. Save it as a WAV file with these specifications:
   - 16-bit mono audio
   - Sample rate of 22050Hz or higher
   - Clear pronunciations with consistent volume

3. Convert your recording to the required format (if needed):
```bash
ffmpeg -i your_recording.mp3 -ar 22050 -ac 1 -acodec pcm_s16le static/voices/creative/voice_6_custom_voice.wav
```

4. Follow the naming convention: `voice_ID_NAME.wav` where:
   - `ID` is a unique number (start with 6 if using the default voices)
   - `NAME` is a descriptive name with underscores instead of spaces

5. Place the file in the `static/voices/creative` directory

---

For more information on using the EchoForge system, refer to the [main documentation](README.md) and the [debugging guide](DEBUGGING_GUIDE.md). 