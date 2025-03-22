#!/bin/bash
# Script to run the EchoForge server with proper cleanup

# Setup colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to log messages
log() {
    local message="$1"
    local color="$2"
    echo -e "${color}${message}${NC}"
}

# Run the stop script if it exists
if [ -f "$SCRIPT_DIR/stop_server.sh" ]; then
    log "Running stop script to clean up existing processes..." "$YELLOW"
    bash "$SCRIPT_DIR/stop_server.sh"
    sleep 2
else
    log "Warning: stop_server.sh not found. Proceeding without cleanup." "$RED"
fi

# Check if virtual environment exists
if [ -d ".venv" ]; then
    # Activate virtual environment
    log "Activating virtual environment..." "$YELLOW"
    source .venv/bin/activate
fi

# Check for required dependencies
if ! command_exists ffmpeg; then
    log "Warning: ffmpeg not found. Audio processing may not work correctly." "$RED"
fi

# Create necessary directories
mkdir -p /tmp/echoforge/voices
log "Ensuring output directory exists: /tmp/echoforge/voices" "$YELLOW"

# Get the default port from config
DEFAULT_PORT=$(python -c "from app.core import config; print(config.DEFAULT_PORT)")
DEFAULT_HOST=$(python -c "from app.core import config; print(config.PUBLIC_HOST if config.ALLOW_PUBLIC_SERVING else config.DEFAULT_HOST)")

# Print server information
log "=================================" "$BLUE"
log "      EchoForge Server          " "$BLUE"
log "=================================" "$BLUE"
log "Host: $DEFAULT_HOST" "$YELLOW"
log "Port: $DEFAULT_PORT" "$YELLOW"
log "Public: $(python -c "from app.core import config; print('Yes' if config.ALLOW_PUBLIC_SERVING else 'No')")" "$YELLOW"
log "Auth: $(python -c "from app.core import config; print('Yes' if config.ENABLE_AUTH else 'No')")" "$YELLOW"
log "Auto-reload: Enabled" "$YELLOW"
echo

# Check GPU availability
if command_exists nvidia-smi; then
    log "Checking GPU status..." "$YELLOW"
    nvidia-smi
else
    log "NVIDIA tools not found. If you're using GPU acceleration, this may cause issues." "$RED"
fi

# Run the server with auto-reload enabled
log "Starting EchoForge server with auto-reload..." "$GREEN"
log "To stop the server, run ./stop_server.sh" "$YELLOW"
echo

# Export environment variables for FFmpeg support
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
log "Set LD_LIBRARY_PATH for FFmpeg support" "$YELLOW"

python run.py --host $DEFAULT_HOST --port $DEFAULT_PORT --reload
