#!/bin/bash
# Setup script for EchoForge using uv

set -e  # Exit immediately if a command exits with a non-zero status

# Setup colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}  EchoForge Environment Setup    ${NC}"
echo -e "${BLUE}=================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}uv is not installed. Installing...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add uv to PATH for this session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    echo -e "${GREEN}uv installed successfully!${NC}"
fi

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
uv venv

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Install dependencies using uv sync
echo -e "${YELLOW}Installing dependencies using uv sync...${NC}"
uv sync

# Install development dependencies if they exist
if [ -f "requirements-dev.txt" ]; then
    echo -e "${YELLOW}Installing development dependencies...${NC}"
    uv pip install -r requirements-dev.txt
fi

# Create .env.local file if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo -e "${YELLOW}Creating .env.local file...${NC}"
    cat > .env.local << EOF
# Local environment settings for EchoForge
# These settings override the defaults in config.py

# Server settings
ALLOW_PUBLIC_SERVING=true
PUBLIC_HOST=0.0.0.0

# Theme settings
DEFAULT_THEME=dark

# Authentication settings
# Uncomment and set these if you want to enable authentication
# ENABLE_AUTH=true
# AUTH_USERNAME=your_username
# AUTH_PASSWORD=your_secure_password

# Output directory
# OUTPUT_DIR=/path/to/your/output/directory

# Model settings
# MODEL_PATH=/path/to/your/model/checkpoint
EOF
    echo -e "${GREEN}.env.local file created. Edit it to customize your environment.${NC}"
else
    echo -e "${GREEN}.env.local file already exists.${NC}"
fi

# Create outputs directory
mkdir -p outputs

echo -e "${GREEN}Environment setup complete!${NC}"
echo -e "${YELLOW}To activate the environment, run:${NC}"
echo -e "    source .venv/bin/activate"
echo
echo -e "${YELLOW}To start the server, run:${NC}"
echo -e "    ./run_server.sh" 