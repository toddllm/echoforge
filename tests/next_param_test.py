#!/usr/bin/env python
"""
Explicit Next Parameter Test for EchoForge Login

This script tests the login endpoint with and without a 'next' parameter
to determine if this is causing the authentication issues.
"""

import os
import sys
import time
import json
import logging
import requests
from urllib.parse import urljoin

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("next_param_test")

# Constants
SERVER_URL = "http://localhost:8765"
TEST_LOGIN_URL = urljoin(SERVER_URL, "/api/auth/test-login")
MAIN_LOGIN_URL = urljoin(SERVER_URL, "/api/auth/login")

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

def test_login_without_next():
    """Test login without a 'next' parameter."""
    logger.info("=" * 80)
    logger.info("TESTING LOGIN WITHOUT 'NEXT' PARAMETER")
    logger.info("=" * 80)
    
    try:
        # Prepare form data
        form_data = {
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
        }
        logger.info(f"Submitting form data to {MAIN_LOGIN_URL}")
        
        # Make a POST request with form data
        response = requests.post(MAIN_LOGIN_URL, data=form_data)
        
        # Log results
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ SUCCESS: Login without 'next' returned 200 OK")
            try:
                logger.info(f"Response JSON: {json.dumps(response.json(), indent=2)}")
            except:
                logger.info(f"Response text: {response.text}")
        else:
            logger.error(f"❌ ERROR: Login without 'next' returned {response.status_code}")
            try:
                logger.error(f"Response content: {json.dumps(response.json(), indent=2)}")
            except:
                logger.error(f"Response text: {response.text}")
            
        return response.status_code == 200
    except Exception as e:
        logger.error(f"❌ Exception during test: {str(e)}")
        return False

def test_login_with_next():
    """Test login with a 'next' parameter."""
    logger.info("=" * 80)
    logger.info("TESTING LOGIN WITH 'NEXT' PARAMETER")
    logger.info("=" * 80)
    
    try:
        # Prepare form data
        form_data = {
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
        }
        
        # Add 'next' parameter to URL
        url_with_next = f"{MAIN_LOGIN_URL}?next=/dashboard"
        logger.info(f"Submitting form data to {url_with_next}")
        
        # Make a POST request with form data and 'next' parameter
        response = requests.post(url_with_next, data=form_data)
        
        # Log results
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ SUCCESS: Login with 'next' returned 200 OK")
            try:
                logger.info(f"Response JSON: {json.dumps(response.json(), indent=2)}")
                logger.info(f"Response headers: {dict(response.headers)}")
                if 'X-Next-URL' in response.headers:
                    logger.info(f"✅ X-Next-URL header found: {response.headers['X-Next-URL']}")
                else:
                    logger.warning("⚠️ X-Next-URL header not found in response")
            except:
                logger.info(f"Response text: {response.text}")
        else:
            logger.error(f"❌ ERROR: Login with 'next' returned {response.status_code}")
            try:
                logger.error(f"Response content: {json.dumps(response.json(), indent=2)}")
            except:
                logger.error(f"Response text: {response.text}")
            
        return response.status_code == 200
    except Exception as e:
        logger.error(f"❌ Exception during test: {str(e)}")
        return False

def test_login_with_next_in_form():
    """Test login with a 'next' parameter in the form data."""
    logger.info("=" * 80)
    logger.info("TESTING LOGIN WITH 'NEXT' PARAMETER IN FORM")
    logger.info("=" * 80)
    
    try:
        # Prepare form data with 'next' parameter
        form_data = {
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "next": "/dashboard"
        }
        
        logger.info(f"Submitting form data (with 'next') to {MAIN_LOGIN_URL}")
        
        # Make a POST request with form data
        response = requests.post(MAIN_LOGIN_URL, data=form_data)
        
        # Log results
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ SUCCESS: Login with 'next' in form returned 200 OK")
            try:
                logger.info(f"Response JSON: {json.dumps(response.json(), indent=2)}")
                logger.info(f"Response headers: {dict(response.headers)}")
                if 'X-Next-URL' in response.headers:
                    logger.info(f"✅ X-Next-URL header found: {response.headers['X-Next-URL']}")
                else:
                    logger.warning("⚠️ X-Next-URL header not found in response")
            except:
                logger.info(f"Response text: {response.text}")
        else:
            logger.error(f"❌ ERROR: Login with 'next' in form returned {response.status_code}")
            try:
                logger.error(f"Response content: {json.dumps(response.json(), indent=2)}")
            except:
                logger.error(f"Response text: {response.text}")
            
        return response.status_code == 200
    except Exception as e:
        logger.error(f"❌ Exception during test: {str(e)}")
        return False

if __name__ == "__main__":
    # Ensure test mode is active
    os.environ["ECHOFORGE_TEST"] = "true"
    logger.info(f"Test mode environment variable: {os.environ.get('ECHOFORGE_TEST')}")
    
    # Ensure server is ready
    if ensure_server_ready(SERVER_URL):
        # Run all three tests
        without_next_result = test_login_without_next()
        with_next_result = test_login_with_next()
        next_in_form_result = test_login_with_next_in_form()
        
        # Summarize results
        logger.info("=" * 80)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Login without 'next': {'✅ PASS' if without_next_result else '❌ FAIL'}")
        logger.info(f"Login with 'next' in URL: {'✅ PASS' if with_next_result else '❌ FAIL'}")
        logger.info(f"Login with 'next' in form: {'✅ PASS' if next_in_form_result else '❌ FAIL'}")
        
        # Determine root of the problem
        if not without_next_result and not with_next_result:
            logger.info("❌ CONCLUSION: The login endpoint fails regardless of the 'next' parameter")
        elif not without_next_result and with_next_result:
            logger.info("❓ CONCLUSION: The login endpoint works WITH a 'next' parameter but fails without it")
        elif without_next_result and not with_next_result:
            logger.info("❓ CONCLUSION: The login endpoint works WITHOUT a 'next' parameter but fails with it")
        elif without_next_result and with_next_result:
            logger.info("✅ CONCLUSION: The login endpoint works correctly with and without 'next' parameter")
        
        # Assessment based on form-based next parameter
        if next_in_form_result:
            logger.info("✅ ADDITIONAL INFO: Login works when 'next' is included in form data")
        else:
            logger.info("❌ ADDITIONAL INFO: Login fails when 'next' is included in form data")
        
        # Exit with appropriate code
        if without_next_result and with_next_result and next_in_form_result:
            logger.info("=" * 80)
            logger.info("✅ ALL TESTS PASSED")
            logger.info("=" * 80)
            sys.exit(0)
        else:
            logger.info("=" * 80)
            logger.info("❌ SOME TESTS FAILED")
            logger.info("=" * 80)
            sys.exit(1)
    else:
        logger.error("Server not ready, exiting.")
        sys.exit(1)
