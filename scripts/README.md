# EchoForge Scripts

This directory contains utility scripts for the EchoForge application.

## Available Scripts

### generate_voice.py

A standalone script for generating voice using the CSM model. This script can be used to quickly generate voice samples without running the full web application.

#### Usage

```bash
python -m scripts.generate_voice --text "Hello, this is a test." --device cpu
```

#### Options

- `--text TEXT`: Text to convert to speech (required)
- `--output OUTPUT`: Output file path (default: auto-generated)
- `--device {cpu,cuda,auto}`: Device to use for generation (default: cpu)
- `--speaker-id SPEAKER_ID`: Speaker ID to use (default: 1)
- `--temperature TEMPERATURE`: Temperature for sampling (default: 0.7)
- `--top-k TOP_K`: Top-k tokens to consider (default: 50)
- `--model-path MODEL_PATH`: Path to model checkpoint (default: auto-download)
- `--verbose`: Enable verbose logging

#### Examples

Generate speech with default settings:
```bash
python -m scripts.generate_voice --text "Hello, this is a test."
```

Generate speech with custom parameters:
```bash
python -m scripts.generate_voice --text "Hello, this is a test." --speaker-id 2 --temperature 0.9 --top-k 80 --device cuda
```

Save output to a specific file:
```bash
python -m scripts.generate_voice --text "Hello, this is a test." --output my_voice.wav
```

## Adding New Scripts

When adding new scripts to this directory, please follow these guidelines:

1. Add a proper shebang line: `#!/usr/bin/env python3`
2. Include a docstring explaining the purpose of the script
3. Add proper argument parsing with help text
4. Add error handling and logging
5. Update this README with information about the new script 