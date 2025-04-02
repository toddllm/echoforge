#!/usr/bin/env python3
"""
Test script for the EchoForge authentication system.

This script performs basic tests on the user authentication functionality.
"""

import os
import sys
import argparse
import logging
import json
import requests
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import EchoForge modules
from app.core.env_loader import load_env_files

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("echoforge.test_auth")

def test_signup(base_url, email, username, password):
    """Test user signup."""
    logger.info(f"Testing signup for user: {username}")
    
    url = f"{base_url}/api/auth/signup"
    data = {
        "email": email,
        "username": username,
        "first_name": "Test",
        "last_name": "User",
        "password": password
    }
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        logger.info("Signup successful!")
        return True
    else:
        logger.error(f"Signup failed with status {response.status_code}: {response.text}")
        return False

def test_login(base_url, username, password):
    """Test user login."""
    logger.info(f"Testing login for user: {username}")
    
    url = f"{base_url}/api/auth/login"
    data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(
        url, 
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        result = response.json()
        token = result.get("access_token")
        logger.info("Login successful!")
        logger.info(f"Received token: {token[:10]}...")
        return token
    else:
        logger.error(f"Login failed with status {response.status_code}: {response.text}")
        return None

def test_profile(base_url, token):
    """Test fetching user profile."""
    logger.info("Testing profile retrieval")
    
    url = f"{base_url}/api/users/profile"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        profile = response.json()
        logger.info(f"Profile retrieved successfully: {json.dumps(profile, indent=2)}")
        return profile
    else:
        logger.error(f"Profile retrieval failed with status {response.status_code}: {response.text}")
        return None

def test_forgot_password(base_url, email):
    """Test forgot password functionality."""
    logger.info(f"Testing forgot password for email: {email}")
    
    url = f"{base_url}/api/auth/forgot-password"
    data = {"email": email}
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        logger.info("Forgot password request sent successfully!")
        return True
    else:
        logger.error(f"Forgot password request failed with status {response.status_code}: {response.text}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test EchoForge authentication system")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL of the EchoForge API")
    parser.add_argument("--email", default="test@example.com", help="Email for testing")
    parser.add_argument("--username", default="testuser", help="Username for testing")
    parser.add_argument("--password", default="Password123!", help="Password for testing")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_env_files()
    
    logger.info("Starting EchoForge authentication tests")
    
    # Test signup
    signup_result = test_signup(args.base_url, args.email, args.username, args.password)
    
    # Test login
    token = test_login(args.base_url, args.username, args.password)
    
    if token:
        # Test profile retrieval
        profile = test_profile(args.base_url, token)
        
        # Test forgot password
        forgot_result = test_forgot_password(args.base_url, args.email)
    
    logger.info("Authentication tests completed")

if __name__ == "__main__":
    main()
