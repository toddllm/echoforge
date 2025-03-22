#!/usr/bin/env python
"""
Redirect Flow Test for EchoForge

This script tests the complete login and redirect flow, simulating a user
logging in and being redirected to a target page.
"""

import os
import sys
import time
import json
import logging
import requests
from urllib.parse import urljoin, urlparse, parse_qs

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("redirect_flow_test")

# Constants
SERVER_URL = "http://localhost:8765"
LOGIN_URL = urljoin(SERVER_URL, "/api/auth/login")
TARGET_URL = "/dashboard"  # Target URL for redirection

# Test data
TEST_USERNAME = "echoforge"
TEST_PASSWORD = "testpassword"

def ensure_server_ready(url, max_attempts=10, delay=1):
    """Ensure server is up and running before running tests."""
    logger.info(f"Checking if server is ready at {url}...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(url)
            if response.status_code < 500:  # Any non-server error is good enough
                logger.info(f"Server is ready! (Status: {response.status_code})")
                return True
        except requests.RequestException:
            pass
        
        logger.info(f"Server not ready, attempt {attempt+1}/{max_attempts}...")
        time.sleep(delay)
    
    logger.error(f"Server not ready after {max_attempts} attempts")
    return False

def test_login_and_redirect_flow():
    """Test the complete login and redirect flow."""
    logger.info("=" * 80)
    logger.info("TESTING COMPLETE LOGIN AND REDIRECT FLOW")
    logger.info("=" * 80)
    
    # Step 1: Create a session to maintain cookies
    session = requests.Session()
    
    try:
        # Step 2: Log in with 'next' parameter
        login_url_with_next = f"{LOGIN_URL}?next={TARGET_URL}"
        logger.info(f"Starting login flow with redirect to: {TARGET_URL}")
        logger.info(f"Login URL: {login_url_with_next}")
        
        form_data = {
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
        }
        
        # Make login request
        login_response = session.post(login_url_with_next, data=form_data)
        logger.info(f"Login response status code: {login_response.status_code}")
        
        if login_response.status_code != 200:
            logger.error(f"Login failed with status code: {login_response.status_code}")
            try:
                logger.error(f"Response content: {json.dumps(login_response.json(), indent=2)}")
            except:
                logger.error(f"Response text: {login_response.text}")
            return False
        
        # Step 3: Check if we got the X-Next-URL header
        logger.info(f"Login successful!")
        logger.info(f"Response headers: {dict(login_response.headers)}")
        
        if 'X-Next-URL' in login_response.headers:
            next_url = login_response.headers['X-Next-URL']
            logger.info(f"✅ X-Next-URL header found: {next_url}")
            full_next_url = urljoin(SERVER_URL, next_url)
            
            # Step 4: Try to access the target URL
            logger.info(f"Attempting to access target URL: {full_next_url}")
            target_response = session.get(full_next_url)
            
            logger.info(f"Target page response status code: {target_response.status_code}")
            
            # Check if access is successful (200 OK) or redirected (30x)
            if 200 <= target_response.status_code < 400:
                logger.info(f"✅ Successfully accessed target page after login")
                return True
            else:
                logger.error(f"❌ Failed to access target page: {target_response.status_code}")
                return False
        else:
            logger.warning("⚠️ X-Next-URL header not found in response")
            return False
            
    except Exception as e:
        logger.error(f"❌ Exception during test: {str(e)}")
        return False

if __name__ == "__main__":
    # Ensure test mode is active
    os.environ["ECHOFORGE_TEST"] = "true"
    logger.info(f"Test mode environment variable: {os.environ.get('ECHOFORGE_TEST')}")
    
    # Ensure server is ready
    if ensure_server_ready(SERVER_URL):
        # Run the redirect flow test
        result = test_login_and_redirect_flow()
        
        # Summarize results
        logger.info("=" * 80)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Login and redirect flow: {'✅ PASS' if result else '❌ FAIL'}")
        
        sys.exit(0 if result else 1)
    else:
        logger.error("Failed to connect to server")
        sys.exit(1)
