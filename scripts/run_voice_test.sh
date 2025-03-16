#!/bin/bash
# Run the voice generation test script

# Change to the project directory
cd "$(dirname "$0")/.."

# Ensure the virtual environment is activated
if [ -d ".venv-uv" ]; then
    echo "Using .venv-uv virtual environment"
    source .venv-uv/bin/activate
elif [ -d ".venv" ]; then
    echo "Using .venv virtual environment"
    source .venv/bin/activate
else
    echo "No virtual environment found"
    exit 1
fi

# Setup default output directory
export OUTPUT_DIR="/tmp/echoforge/voices"

# Ensure the output directory exists
mkdir -p "$OUTPUT_DIR/admin"
echo "Using output directory: $OUTPUT_DIR"

# Run the test script with CPU by default for reliability
python scripts/test_admin_voice.py --device cpu "$@"

# Deactivate the virtual environment
deactivate 