# EchoForge Voice Setup Guide

This document provides detailed instructions for setting up the voice generation system in EchoForge, including how to generate high-quality voice samples using the CSM model.

## Quick Start

For basic setup with placeholder voices (no special dependencies required):
```bash
python setup_voices.py
```

For high-quality voice generation with the CSM model:
```bash
# Install required dependencies
pip install -r csm-voice-cloning/requirements.txt

# Generate voices (use GPU if available)
python setup_voices.py --force
```

## Requirements for High-Quality Voice Generation

The setup script can generate voices in two ways:
1. **Basic mode**: Simple sine wave generation (works on any system)
2. **CSM mode**: High-quality neural voice generation (requires specific dependencies)

### Dependencies for CSM Voice Generation

For high-quality voices, you need the following:

1. **csm-voice-cloning directory**: 
   - This should be present in your EchoForge root directory
   - Contains the necessary model files and scripts

2. **Python packages**:
   ```
   torch==2.4.0
   torchaudio==2.4.0
   tokenizers==0.21.0
   transformers==4.49.0
   huggingface_hub==0.28.1
   moshi==0.2.2
   torchtune==0.4.0
   torchao==0.9.0
   silentcipher @ git+https://github.com/SesameAILabs/silentcipher@master
   ```

Install all required packages with:
```bash
pip install -r csm-voice-cloning/requirements.txt
```

## Command-Line Options

The setup script supports these options:

- `--force`: Regenerate voice files even if they already exist
- `--cpu`: Force CPU usage instead of GPU (slower but works on all systems)
- `--skip-deps-check`: Skip dependency checks and attempt to run anyway

## Troubleshooting

If you encounter issues during voice generation:

### "CSM voice generation modules not found"

This means the script couldn't find or import from the csm-voice-cloning directory.

**Solution**: 
- Ensure the csm-voice-cloning directory exists in the EchoForge root
- Check that it contains all required files (generator.py, models.py, etc.)

### "Additional dependencies for CSM not found"

This means you're missing some required Python packages.

**Solution**:
```bash
pip install -r csm-voice-cloning/requirements.txt
```

### "CUDA not available, falling back to CPU"

This is just informational - the script will use CPU instead of GPU.

**Solution**:
- If you want to use GPU, ensure CUDA is properly installed
- If you want to use CPU without this message, add the `--cpu` flag

## Generated Voices

The script generates voice files for 5 different characters:

1. **Commander Sterling**: Deep authoritative male voice
2. **Dr. Elise Jensen**: Clear, articulate female voice
3. **James Fletcher**: Warm, friendly male voice
4. **Sophia Chen**: Energetic female voice with varied intonation
5. **Morgan Riley**: Balanced, neutral voice

Each voice has 3 variants (1 primary + 2 variations) to provide options.

## Testing the Voices

After generating voices, you can test them using:

1. Start the EchoForge server:
   ```bash
   ./start_server.sh
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8765/debug
   ```

3. Use the debug interface to test different voices with your own text input

## Advanced: Creating Custom Voices

To create custom voices, you can modify the `VOICE_CONFIGS` list in `setup_voices.py`.

For each voice, you can configure:
- `speaker_id`: Which CSM base voice to use (0-7)
- `temperature`: Controls randomness/creativity (0.8-1.2)
- `topk`: Controls vocabulary diversity (40-60)
- `sample_text`: The text used to generate the sample

Then run:
```bash
python setup_voices.py --force
``` 