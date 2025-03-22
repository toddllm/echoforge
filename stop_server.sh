#!/bin/bash
#
# EchoForge Server Stop Script
# This script gracefully shuts down the EchoForge server and cleans up all related processes

# Set strict error handling
set -e

echo "===== Stopping EchoForge Server ====="
echo "$(date): Beginning shutdown process"

# Define log file
LOG_DIR="/home/tdeshane/echoforge/logs"
LOG_FILE="${LOG_DIR}/shutdown_$(date +%Y%m%d_%H%M%S).log"

# Create logs directory if it doesn't exist
mkdir -p "${LOG_DIR}"

# Function to log messages
log() {
    local message="$1"
    echo "$(date +"%Y-%m-%d %H:%M:%S") - $message" | tee -a "${LOG_FILE}"
}

# Function to check if process exists
process_exists() {
    ps -p "$1" > /dev/null 2>&1
    return $?
}

# Kill processes by name pattern
kill_processes_by_pattern() {
    local pattern="$1"
    local signal="$2"
    local processes
    
    log "Searching for processes matching pattern: $pattern"
    processes=$(pgrep -f "$pattern" 2>/dev/null || true)
    
    if [ -z "$processes" ]; then
        log "No processes found matching pattern: $pattern"
        return 0
    fi
    
    log "Found processes: $processes"
    
    for pid in $processes; do
        if process_exists "$pid"; then
            log "Sending $signal signal to process $pid ($(ps -p "$pid" -o comm=))"
            kill -"$signal" "$pid" 2>/dev/null || log "Failed to send $signal to $pid"
        fi
    done
}

# Clean up GPU resources
cleanup_gpu() {
    log "Checking for GPU processes..."
    
    # Check if nvidia-smi is available
    if command -v nvidia-smi >/dev/null 2>&1; then
        log "Running nvidia-smi to check GPU usage"
        nvidia-smi >> "${LOG_FILE}" 2>&1 || true
        
        # This is a more aggressive approach if needed in the future
        # nvidia-cuda-mps-control -d
        # echo quit | nvidia-cuda-mps-control
    else
        log "nvidia-smi not available, skipping GPU cleanup"
    fi
}

# Main shutdown sequence
main() {
    log "Starting EchoForge shutdown sequence"
    
    # 1. Gracefully stop FastAPI/Uvicorn server processes
    log "Attempting graceful shutdown of FastAPI/Uvicorn processes"
    kill_processes_by_pattern "uvicorn.*app.main" TERM
    kill_processes_by_pattern "python.*app.main" TERM
    sleep 2
    
    # 2. Stop EchoForge-specific processes
    log "Stopping EchoForge-specific processes"
    kill_processes_by_pattern "echoforge" TERM
    sleep 2
    
    # 3. Force kill any remaining processes if they're still running
    log "Checking for remaining processes and force killing if necessary"
    kill_processes_by_pattern "uvicorn.*app.main" KILL
    kill_processes_by_pattern "python.*app.main" KILL
    kill_processes_by_pattern "echoforge" KILL
    sleep 1
    
    # 4. Clean up GPU resources
    cleanup_gpu
    
    # 5. Verify everything is stopped
    if pgrep -f "uvicorn.*app.main" >/dev/null 2>&1 || \
       pgrep -f "python.*app.main" >/dev/null 2>&1 || \
       pgrep -f "echoforge" >/dev/null 2>&1; then
        log "WARNING: Some processes may still be running"
    else
        log "All EchoForge processes successfully terminated"
    fi
    
    log "Shutdown sequence completed"
    echo "===== EchoForge Server Stopped ====="
}

# Run the main function
main
