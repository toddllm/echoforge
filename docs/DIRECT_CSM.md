# Direct CSM Implementation

This document describes the direct CSM (Conversational Speech Model) implementation in EchoForge, which provides high-quality voice generation.

## Overview

The direct CSM implementation bypasses adapter layers and directly uses the CSM model from the `tts_poc/voice_poc/csm` directory. This approach offers several advantages:

- **Improved Performance**: Direct access to the model reduces overhead
- **Better Audio Quality**: Fewer transformations lead to clearer voice output
- **Simplified Architecture**: Reduces complexity in the voice generation pipeline
- **Fallback Mechanisms**: Automatic fallback to CPU if CUDA fails

## Architecture

The implementation consists of the following components:

1. **DirectCSM Class**: Core implementation that handles model loading and speech generation
2. **Voice Generator Integration**: Updated to prioritize the direct CSM implementation
3. **Configuration**: Updated to use the correct model checkpoint path
4. **Testing Scripts**: Enhanced to support various generation parameters

## Usage

### API Endpoint

The direct CSM implementation is automatically used by the voice generation API endpoint:

```
POST /api/generate
```

Example request:
```json
{
  "text": "This is a test of the voice generation system.",
  "speaker_id": 1,
  "temperature": 0.7,
  "top_k": 50,
  "device": "cuda",
  "style": "default"
}
```

### Command Line

You can also use the test script to generate voices directly:

```bash
./scripts/test_voice_api.py "Your text here" --temperature 0.9 --top-k 40 --device cuda
```

Or use the direct CSM test script:

```bash
./scripts/direct_csm_test.py "Your text here"
```

## Parameters

The following parameters can be adjusted to control voice generation:

- **temperature**: Controls randomness (0.5-1.0, higher = more diverse)
- **top_k**: Number of highest probability tokens to consider (30-50)
- **device**: Hardware to use for inference ("cuda" or "cpu")
- **speaker_id**: Speaker voice to use (currently only 1 is supported)

## Implementation Details

### Model Loading

The DirectCSM class automatically finds and loads the CSM model checkpoint:

1. First checks the default location in the CSM directory
2. Then looks for the specific Hugging Face cache path for CSM-1B
3. Finally searches the general Hugging Face cache

### Speech Generation

The speech generation process:

1. Initializes the model if not already initialized
2. Generates speech using the CSM model's generate method
3. Handles CUDA errors by falling back to CPU if needed
4. Returns the audio tensor and sample rate

### Audio Saving

The generated audio is saved to the configured output directory:

1. Ensures the audio tensor is on CPU
2. Saves the audio using torchaudio
3. Creates a symlink for easy access to the latest generated file

## Troubleshooting

If you encounter issues with voice generation:

1. **Check CUDA Availability**: Ensure CUDA is available if using GPU
2. **Memory Issues**: If CUDA out of memory errors occur, try CPU instead
3. **Model Checkpoint**: Verify the model checkpoint path is correct
4. **Audio Quality**: If audio quality is poor, try adjusting temperature and top_k

## Future Improvements

- Support for multiple speakers
- Voice style customization
- Streaming audio output
- Batch processing for multiple voice generations 