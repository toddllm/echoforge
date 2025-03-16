# EchoForge Examples

This directory contains example scripts that demonstrate how to use the EchoForge application.

## CSM Model Example

The `csm_model_example.py` script demonstrates how to use the CSM model for text-to-speech generation.

### Usage

```bash
# Basic usage
./csm_model_example.py

# Custom text
./csm_model_example.py --text "Hello, this is a custom text."

# Custom speaker ID
./csm_model_example.py --speaker-id 2

# Custom temperature and top-k
./csm_model_example.py --temperature 0.7 --top-k 30

# Custom output file
./csm_model_example.py --output "custom_output.wav"

# Use placeholder model
./csm_model_example.py --use-placeholder

# Specify device
./csm_model_example.py --device cpu
```

### Options

- `--text`: Text to convert to speech (default: "Hello, world! This is a test of the CSM model.")
- `--speaker-id`: Speaker ID to use (default: 1)
- `--temperature`: Temperature for sampling (default: 0.9)
- `--top-k`: Top-k for sampling (default: 50)
- `--device`: Device to use (cuda or cpu, default: auto-detect)
- `--output`: Output file path (default: "output.wav")
- `--use-placeholder`: Use placeholder model instead of real model

## Running the Examples

To run the examples, make sure you have activated the virtual environment and installed the required dependencies:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the example
cd examples
./csm_model_example.py
``` 