#!/bin/bash
# Script to run the EchoForge server

# Setup colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ -d ".venv" ]; then
    # Activate virtual environment
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Get the default port from config
DEFAULT_PORT=$(python -c "from app.core import config; print(config.DEFAULT_PORT)")
DEFAULT_HOST=$(python -c "from app.core import config; print(config.PUBLIC_HOST if config.ALLOW_PUBLIC_SERVING else config.DEFAULT_HOST)")

# Print server information
echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}      EchoForge Server          ${NC}"
echo -e "${BLUE}=================================${NC}"
echo -e "${YELLOW}Host:${NC} $DEFAULT_HOST"
echo -e "${YELLOW}Port:${NC} $DEFAULT_PORT"
echo -e "${YELLOW}Public:${NC} $(python -c "from app.core import config; print('Yes' if config.ALLOW_PUBLIC_SERVING else 'No')")"
echo -e "${YELLOW}Auth:${NC} $(python -c "from app.core import config; print('Yes' if config.ENABLE_AUTH else 'No')")"
echo -e "${YELLOW}Auto-reload:${NC} Enabled"
echo

# Run the server with auto-reload enabled
echo -e "${GREEN}Starting EchoForge server with auto-reload...${NC}"
python run.py --host $DEFAULT_HOST --port $DEFAULT_PORT --reload 