#!/usr/bin/env python3
"""
Test script for Direct CSM integration in the admin page.

This script tests the Direct CSM integration in the admin page by:
1. Enabling Direct CSM in the config
2. Testing the Direct CSM implementation
3. Generating a voice using Direct CSM
"""

import os
import sys
import time
import json
import requests
from pathlib import Path

# Add the project root to the path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

# Import EchoForge modules
from app.core import config
from app.models import create_direct_csm, DirectCSMError

# Server URL
SERVER_URL = f"http://{config.HOST}:{config.PORT}"
ADMIN_API_URL = f"{SERVER_URL}/api/admin"
API_URL = f"{SERVER_URL}/api"

# Authentication
AUTH_USERNAME = config.AUTH_USERNAME
AUTH_PASSWORD = config.AUTH_PASSWORD
AUTH = (AUTH_USERNAME, AUTH_PASSWORD)

# Test text
TEST_TEXT = "This is a test of the Direct CSM implementation in the admin page. The voice should be clear and natural sounding."

def test_direct_csm_config():
    """Test Direct CSM configuration."""
    print("Testing Direct CSM configuration...")
    
    # Check if Direct CSM is enabled in config
    if not config.USE_DIRECT_CSM:
        print("Direct CSM is not enabled in config. Enabling it...")
        config.USE_DIRECT_CSM = True
        print("Direct CSM enabled in config.")
    else:
        print("Direct CSM is already enabled in config.")
    
    # Check if Direct CSM path exists
    if not os.path.exists(config.DIRECT_CSM_PATH):
        print(f"ERROR: Direct CSM path does not exist: {config.DIRECT_CSM_PATH}")
        return False
    
    # Check if required files exist
    required_files = ["generator.py", "models.py"]
    for file in required_files:
        file_path = os.path.join(config.DIRECT_CSM_PATH, file)
        if not os.path.exists(file_path):
            print(f"ERROR: Required file does not exist: {file_path}")
            return False
    
    print("Direct CSM configuration is valid.")
    return True

def test_direct_csm_api():
    """Test Direct CSM API endpoints."""
    print("\nTesting Direct CSM API endpoints...")
    
    # Test getting Direct CSM info
    try:
        response = requests.get(f"{ADMIN_API_URL}/models/direct-csm-info", auth=AUTH)
        if response.status_code != 200:
            print(f"ERROR: Failed to get Direct CSM info. Status code: {response.status_code}")
            return False
        
        info = response.json()
        print(f"Direct CSM info: {json.dumps(info, indent=2)}")
        
        # Test toggling Direct CSM
        print("\nTesting toggling Direct CSM...")
        current_state = info["enabled"]
        
        # Toggle off
        response = requests.post(
            f"{ADMIN_API_URL}/models/toggle-direct-csm",
            json={"enable": False},
            auth=AUTH
        )
        if response.status_code != 200:
            print(f"ERROR: Failed to toggle Direct CSM off. Status code: {response.status_code}")
            return False
        
        print("Direct CSM toggled off successfully.")
        
        # Toggle back on
        response = requests.post(
            f"{ADMIN_API_URL}/models/toggle-direct-csm",
            json={"enable": True},
            auth=AUTH
        )
        if response.status_code != 200:
            print(f"ERROR: Failed to toggle Direct CSM on. Status code: {response.status_code}")
            return False
        
        print("Direct CSM toggled on successfully.")
        
        # Test Direct CSM
        print("\nTesting Direct CSM implementation...")
        response = requests.post(f"{ADMIN_API_URL}/models/test-direct-csm", auth=AUTH)
        if response.status_code != 200:
            print(f"ERROR: Failed to test Direct CSM. Status code: {response.status_code}")
            return False
        
        task_data = response.json()
        task_id = task_data.get("task_id")
        
        if not task_id:
            print("ERROR: No task ID returned from test Direct CSM endpoint.")
            return False
        
        print(f"Direct CSM test started. Task ID: {task_id}")
        
        # Wait for the test to complete
        print("Waiting for the test to complete (20 seconds)...")
        time.sleep(20)
        
        # Check if the test directory exists
        test_dir = os.path.join(config.OUTPUT_DIR, "test")
        if not os.path.exists(test_dir):
            print(f"ERROR: Test directory does not exist: {test_dir}")
            return False
        
        # Check if there are any WAV files in the test directory
        wav_files = [f for f in os.listdir(test_dir) if f.endswith(".wav")]
        if not wav_files:
            print(f"ERROR: No WAV files found in test directory: {test_dir}")
            return False
        
        # Get the most recent WAV file
        wav_files.sort(key=lambda f: os.path.getmtime(os.path.join(test_dir, f)), reverse=True)
        latest_wav = wav_files[0]
        wav_path = os.path.join(test_dir, latest_wav)
        
        print(f"Found test audio file: {wav_path}")
        
        # Check if the file is accessible via the API
        wav_url = f"{SERVER_URL}/voices/test/{latest_wav}"
        response = requests.head(wav_url, auth=AUTH)
        if response.status_code != 200:
            print(f"ERROR: Failed to access test audio file via API. Status code: {response.status_code}")
            return False
        
        print(f"Test audio file is accessible via API: {wav_url}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Exception during Direct CSM API test: {e}")
        return False

def test_voice_generation():
    """Test voice generation using Direct CSM."""
    print("\nTesting voice generation using Direct CSM...")
    
    try:
        # Generate voice using admin API
        response = requests.post(
            f"{ADMIN_API_URL}/generate-voice",
            json={
                "text": TEST_TEXT,
                "speaker_id": config.DEFAULT_SPEAKER_ID,
                "temperature": config.DEFAULT_TEMPERATURE,
                "top_k": config.DEFAULT_TOP_K,
                "style": config.DEFAULT_STYLE,
                "device": config.DEFAULT_DEVICE
            },
            auth=AUTH
        )
        
        if response.status_code != 200:
            print(f"ERROR: Failed to generate voice. Status code: {response.status_code}")
            return False
        
        task_data = response.json()
        task_id = task_data.get("task_id")
        
        if not task_id:
            print("ERROR: No task ID returned from generate voice endpoint.")
            return False
        
        print(f"Voice generation started. Task ID: {task_id}")
        
        # Wait for the voice generation to complete
        print("Waiting for voice generation to complete (20 seconds)...")
        time.sleep(20)
        
        # Check if the admin directory exists
        admin_dir = os.path.join(config.OUTPUT_DIR, "admin")
        if not os.path.exists(admin_dir):
            print(f"ERROR: Admin directory does not exist: {admin_dir}")
            return False
        
        # Check if there are any WAV files in the admin directory
        wav_files = [f for f in os.listdir(admin_dir) if f.endswith(".wav")]
        if not wav_files:
            print(f"ERROR: No WAV files found in admin directory: {admin_dir}")
            return False
        
        # Get the most recent WAV file
        wav_files.sort(key=lambda f: os.path.getmtime(os.path.join(admin_dir, f)), reverse=True)
        latest_wav = wav_files[0]
        wav_path = os.path.join(admin_dir, latest_wav)
        
        print(f"Found voice file: {wav_path}")
        
        # Check if the file is accessible via the API
        wav_url = f"{SERVER_URL}/voices/admin/{latest_wav}"
        response = requests.head(wav_url, auth=AUTH)
        if response.status_code != 200:
            print(f"ERROR: Failed to access voice file via API. Status code: {response.status_code}")
            return False
        
        print(f"Voice file is accessible via API: {wav_url}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Exception during voice generation test: {e}")
        return False

def main():
    """Main function."""
    print("=== Direct CSM Admin Integration Test ===\n")
    
    # Test Direct CSM configuration
    if not test_direct_csm_config():
        print("\nDirect CSM configuration test failed.")
        return 1
    
    # Test Direct CSM API
    if not test_direct_csm_api():
        print("\nDirect CSM API test failed.")
        return 1
    
    # Test voice generation
    if not test_voice_generation():
        print("\nVoice generation test failed.")
        return 1
    
    print("\n=== All tests passed! ===")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 