#!/usr/bin/env python3
"""
Server configuration test script for EchoForge.

This script tests various server startup configurations to ensure the application
can start with different port, host, and authentication settings.
"""

import os
import sys
import time
import argparse
import subprocess
import requests
import signal
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("server_tests")

# Find the project root (assuming this script is in the tests directory)
PROJECT_ROOT = Path(__file__).parent.parent
SERVER_SCRIPT = PROJECT_ROOT / "run.py"

class ServerTest:
    """Test harness for server configuration testing."""
    
    def __init__(self, debug=False):
        """Initialize the server test harness."""
        self.debug = debug
        self.process = None
        self.passed_tests = 0
        self.failed_tests = 0
        self.env = os.environ.copy()
        self.env["ECHOFORGE_TEST"] = "true"  # Enable test mode
    
    def start_server(self, port=8000, host="127.0.0.1", auth_user=None, auth_pass=None, public=False):
        """Start the server with the given configuration."""
        cmd = [sys.executable, str(SERVER_SCRIPT)]
        
        # Add command line arguments
        cmd.extend(["--port", str(port)])
        cmd.extend(["--host", host])
        
        if auth_user and auth_pass:
            cmd.extend(["--auth-user", auth_user])
            cmd.extend(["--auth-pass", auth_pass])
            
        if public:
            cmd.append("--public")
            
        logger.info(f"Starting server with command: {' '.join(cmd)}")
        
        # Start the server process
        self.process = subprocess.Popen(
            cmd,
            env=self.env,
            stdout=subprocess.PIPE if not self.debug else None,
            stderr=subprocess.PIPE if not self.debug else None
        )
        
        # Give the server time to start (increased from 3 to 10 seconds)
        time.sleep(5)
        
        # Wait for server to be responsive
        start_time = time.time()
        while time.time() - start_time < 15:  # Wait up to 15 seconds
            if self.process.poll() is not None:
                # Process has terminated
                return False
                
            # Try to connect to the health endpoint
            try:
                response = requests.get(f"http://{host}:{port}/api/health", timeout=2)
                if response.status_code == 200:
                    logger.info(f"Server started successfully on port {port}")
                    return True
            except requests.RequestException:
                # Connection failed, wait and retry
                time.sleep(1)
                
        return self.process.poll() is None
    
    def stop_server(self):
        """Stop the server if it's running."""
        if self.process:
            logger.info("Stopping server...")
            self.process.send_signal(signal.SIGINT)
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Server didn't stop gracefully, killing...")
                self.process.kill()
            self.process = None
            time.sleep(1)  # Give server time to shut down
    
    def test_server_response(self, port=8000, host="127.0.0.1", path="/", auth=None, expected_status=200):
        """Test server response at the specified path."""
        url = f"http://{host}:{port}{path}"
        try:
            logger.info(f"Testing URL: {url}")
            if auth:
                response = requests.get(url, auth=auth, timeout=5)
            else:
                response = requests.get(url, timeout=5)
            
            if response.status_code == expected_status:
                logger.info(f"✅ Test passed: Got expected status {expected_status}")
                self.passed_tests += 1
                return True
            else:
                logger.error(f"❌ Test failed: Expected status {expected_status}, got {response.status_code}")
                self.failed_tests += 1
                return False
        except requests.RequestException as e:
            logger.error(f"❌ Test failed: Request error: {e}")
            self.failed_tests += 1
            return False
    
    def run_tests(self):
        """Run all server configuration tests."""
        try:
            # Test 1: Basic server startup with default settings
            logger.info("\n==== Test 1: Basic server startup ====")
            if self.start_server():
                self.test_server_response()
                self.test_server_response(path="/api/voices", expected_status=200)
            else:
                logger.error("❌ Server failed to start with default settings")
                self.failed_tests += 1
            self.stop_server()
            
            # Test 2: Server with custom port
            logger.info("\n==== Test 2: Custom port ====")
            if self.start_server(port=8888):
                self.test_server_response(port=8888)
            else:
                logger.error("❌ Server failed to start with custom port")
                self.failed_tests += 1
            self.stop_server()
            
            # Test 3: Server with authentication
            logger.info("\n==== Test 3: Authentication ====")
            if self.start_server(auth_user="testuser", auth_pass="testpass"):
                # Test with wrong auth - should fail
                self.test_server_response(auth=("wrong", "wrong"), expected_status=401)
                # Test with correct auth - should succeed
                self.test_server_response(auth=("testuser", "testpass"), expected_status=200)
            else:
                logger.error("❌ Server failed to start with authentication")
                self.failed_tests += 1
            self.stop_server()
            
            # Test 4: Public server
            logger.info("\n==== Test 4: Public server ====")
            if self.start_server(host="0.0.0.0", public=True):
                # We can only test localhost access since this is automated
                self.test_server_response(host="127.0.0.1")
            else:
                logger.error("❌ Server failed to start in public mode")
                self.failed_tests += 1
            self.stop_server()
            
            # Print results
            total = self.passed_tests + self.failed_tests
            logger.info("\n==== Test Results ====")
            logger.info(f"Passed: {self.passed_tests}/{total}")
            logger.info(f"Failed: {self.failed_tests}/{total}")
            
            return self.failed_tests == 0
        
        finally:
            # Make sure server is stopped if tests are interrupted
            self.stop_server()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run server configuration tests for EchoForge")
    parser.add_argument("--debug", action="store_true", help="Show server output")
    args = parser.parse_args()
    
    try:
        test_harness = ServerTest(debug=args.debug)
        success = test_harness.run_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted")
        sys.exit(130) 