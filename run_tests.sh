#!/bin/bash
# EchoForge Test Runner Script
# This script runs server configuration tests and API tests

set -e  # Exit immediately if a command exits with a non-zero status

# Setup colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}  EchoForge Automated Test Suite ${NC}"
echo -e "${BLUE}=================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Get the default port from config
DEFAULT_PORT=$(python -c "from app.core import config; print(config.DEFAULT_PORT)")
TEST_PORT=$((DEFAULT_PORT + 1))  # Use a different port for testing

# Setup environment for testing
export ECHOFORGE_TEST=true

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"
LOG_FILE="$SCRIPT_DIR/logs/test_run_$(date +%Y%m%d_%H%M%S).log"
SERVER_LOG="$SCRIPT_DIR/logs/server_$(date +%Y%m%d_%H%M%S).log"

echo -e "${YELLOW}Test logs will be saved to:${NC} $LOG_FILE"
echo -e "${YELLOW}Using port ${TEST_PORT} for tests${NC}"
echo

# Function to check if a server is running on a port
wait_for_server() {
    HOST=$1
    PORT=$2
    TIMEOUT=$3
    
    echo -e "${YELLOW}Waiting for server to be ready at ${HOST}:${PORT} (timeout: ${TIMEOUT}s)...${NC}"
    
    ELAPSED=0
    while [ $ELAPSED -lt $TIMEOUT ]; do
        if curl -s -o /dev/null "http://${HOST}:${PORT}/api/health"; then
            echo -e "${GREEN}Server is ready!${NC}"
            return 0
        fi
        sleep 1
        ELAPSED=$((ELAPSED+1))
        echo -n "."
    done
    
    echo
    echo -e "${RED}Timed out waiting for server to start${NC}"
    return 1
}

# Function to run a test and check its exit code
run_test() {
    TEST_NAME=$1
    TEST_CMD=$2
    
    echo -e "${YELLOW}Running ${TEST_NAME}...${NC}"
    echo "Running $TEST_NAME with command: $TEST_CMD" >> "$LOG_FILE"
    
    if eval "$TEST_CMD" >> "$LOG_FILE" 2>&1; then
        echo -e "${GREEN}✓ ${TEST_NAME} passed${NC}"
        return 0
    else
        echo -e "${RED}✗ ${TEST_NAME} failed${NC}"
        echo -e "${YELLOW}See log file for details: ${LOG_FILE}${NC}"
        return 1
    fi
}

# Function to start the server in the background
start_test_server() {
    PORT=$1
    
    echo -e "${YELLOW}Starting test server on port ${PORT}...${NC}"
    
    # Kill any existing processes on the test port
    fuser -k ${PORT}/tcp 2>/dev/null || true
    
    # Create a PID file to track the server process
    PID_FILE="/tmp/echoforge_test_server.pid"
    
    # Run with nohup to ensure it stays running in the background
    cd "$SCRIPT_DIR"
    nohup python run.py --port ${PORT} --auth-user testuser --auth-pass testpass --host 127.0.0.1 > "$SERVER_LOG" 2>&1 &
    SERVER_PID=$!
    
    # Save the PID to a file
    echo $SERVER_PID > $PID_FILE
    
    # Make sure the process is actually started
    if [ -z "$SERVER_PID" ] || ! ps -p $SERVER_PID > /dev/null; then
        echo -e "${RED}Failed to start server process${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Server process started with PID: $SERVER_PID${NC}"
    
    # Wait for server to start (with timeout)
    if wait_for_server "localhost" ${PORT} 20; then
        return 0
    else
        echo -e "${RED}Failed to start the test server, check the logs for details${NC}"
        cat "$SERVER_LOG"
        return 1
    fi
}

# Function to stop the server
stop_test_server() {
    PID_FILE="/tmp/echoforge_test_server.pid"
    
    if [ -f "$PID_FILE" ]; then
        SERVER_PID=$(cat "$PID_FILE")
        
        if [ -n "$SERVER_PID" ] && ps -p $SERVER_PID > /dev/null; then
            echo -e "${YELLOW}Stopping test server (PID: $SERVER_PID)...${NC}"
            kill $SERVER_PID
            sleep 2
            # Force kill if still running
            if ps -p $SERVER_PID > /dev/null; then
                echo -e "${YELLOW}Force killing server process...${NC}"
                kill -9 $SERVER_PID 2>/dev/null || true
            fi
        fi
        
        rm -f "$PID_FILE"
    fi
    
    # Make sure no other processes are using the test port
    fuser -k ${TEST_PORT}/tcp 2>/dev/null || true
}

# Clean up servers on script exit
cleanup() {
    echo -e "${YELLOW}Cleaning up test environment...${NC}"
    stop_test_server
}

# Register cleanup function to run on exit
trap cleanup EXIT INT TERM

# Variable to track overall test status
TESTS_PASSED=true

# Start the test server
if ! start_test_server ${TEST_PORT}; then
    echo -e "${RED}Failed to start test server, aborting tests${NC}"
    exit 1
fi

# Run API tests
if run_test "API Tests" "python $SCRIPT_DIR/tests/test_api.py --url http://localhost:${TEST_PORT} --user testuser --password testpass"; then
    API_TESTS_PASSED=true
else
    API_TESTS_PASSED=false
    TESTS_PASSED=false
fi

# Stop the test server
stop_test_server

# Print summary
echo
echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}        Test Summary            ${NC}"
echo -e "${BLUE}=================================${NC}"
echo -e "API Tests: $(if $API_TESTS_PASSED; then echo -e "${GREEN}PASSED${NC}"; else echo -e "${RED}FAILED${NC}"; fi)"
echo

if $TESTS_PASSED; then
    echo -e "${GREEN}All tests passed successfully!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Check the log file for details:${NC}"
    echo -e "${YELLOW}$LOG_FILE${NC}"
    exit 1
fi 