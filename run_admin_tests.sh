#!/bin/bash
# EchoForge Admin Dashboard Test Runner Script
# This script runs tests for the admin dashboard

set -e  # Exit immediately if a command exits with a non-zero status

# Setup colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  EchoForge Admin Dashboard Test Suite   ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Setup environment for testing
export ECHOFORGE_TEST=true

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"
LOG_FILE="$SCRIPT_DIR/logs/admin_test_run_$(date +%Y%m%d_%H%M%S).log"

echo -e "${YELLOW}Test logs will be saved to:${NC} $LOG_FILE"
echo

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

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Setting up environment...${NC}"
    ./setup_env.sh
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Install test dependencies if needed
echo -e "${YELLOW}Installing test dependencies...${NC}"
pip install pytest pytest-asyncio httpx pytest-cov

# Variable to track overall test status
TESTS_PASSED=true

# Run UI tests for admin routes
if run_test "Admin UI Routes Tests" "python -m pytest tests/ui/test_admin_routes.py -v"; then
    UI_TESTS_PASSED=true
else
    UI_TESTS_PASSED=false
    TESTS_PASSED=false
fi

# Run API tests for admin endpoints
if run_test "Admin API Tests" "python -m pytest tests/api/test_admin_api.py -v"; then
    API_TESTS_PASSED=true
else
    API_TESTS_PASSED=false
    TESTS_PASSED=false
fi

# Run integration tests for admin dashboard
if run_test "Admin Integration Tests" "python -m pytest tests/integration/test_admin_dashboard.py -v"; then
    INTEGRATION_TESTS_PASSED=true
else
    INTEGRATION_TESTS_PASSED=false
    TESTS_PASSED=false
fi

# Run end-to-end tests for admin dashboard
if run_test "Admin E2E Tests" "python -m pytest tests/e2e/test_admin_e2e.py -v"; then
    E2E_TESTS_PASSED=true
else
    E2E_TESTS_PASSED=false
    TESTS_PASSED=false
fi

# Run JavaScript tests for admin dashboard
if run_test "Admin JavaScript Tests" "python -m pytest tests/ui/test_admin_js.py -v"; then
    JS_TESTS_PASSED=true
else
    JS_TESTS_PASSED=false
    TESTS_PASSED=false
fi

# Run authentication tests for admin dashboard
if run_test "Admin Authentication Tests" "python -m pytest tests/ui/test_admin_auth.py -v"; then
    AUTH_TESTS_PASSED=true
else
    AUTH_TESTS_PASSED=false
    TESTS_PASSED=false
fi

# Run error handling tests for admin dashboard
if run_test "Admin Error Handling Tests" "python -m pytest tests/ui/test_admin_errors.py -v"; then
    ERROR_TESTS_PASSED=true
else
    ERROR_TESTS_PASSED=false
    TESTS_PASSED=false
fi

# Print summary
echo
echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}        Test Summary            ${NC}"
echo -e "${BLUE}=================================${NC}"
echo -e "Admin UI Routes Tests: $(if $UI_TESTS_PASSED; then echo -e "${GREEN}PASSED${NC}"; else echo -e "${RED}FAILED${NC}"; fi)"
echo -e "Admin API Tests: $(if $API_TESTS_PASSED; then echo -e "${GREEN}PASSED${NC}"; else echo -e "${RED}FAILED${NC}"; fi)"
echo -e "Admin Integration Tests: $(if $INTEGRATION_TESTS_PASSED; then echo -e "${GREEN}PASSED${NC}"; else echo -e "${RED}FAILED${NC}"; fi)"
echo -e "Admin E2E Tests: $(if $E2E_TESTS_PASSED; then echo -e "${GREEN}PASSED${NC}"; else echo -e "${RED}FAILED${NC}"; fi)"
echo -e "Admin JavaScript Tests: $(if $JS_TESTS_PASSED; then echo -e "${GREEN}PASSED${NC}"; else echo -e "${RED}FAILED${NC}"; fi)"
echo -e "Admin Authentication Tests: $(if $AUTH_TESTS_PASSED; then echo -e "${GREEN}PASSED${NC}"; else echo -e "${RED}FAILED${NC}"; fi)"
echo -e "Admin Error Handling Tests: $(if $ERROR_TESTS_PASSED; then echo -e "${GREEN}PASSED${NC}"; else echo -e "${RED}FAILED${NC}"; fi)"
echo

if $TESTS_PASSED; then
    echo -e "${GREEN}All admin dashboard tests passed successfully!${NC}"
    exit 0
else
    echo -e "${RED}Some admin dashboard tests failed. Check the log file for details:${NC}"
    echo -e "${YELLOW}$LOG_FILE${NC}"
    exit 1
fi 