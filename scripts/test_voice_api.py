#!/usr/bin/env python3
"""
Script to test the voice generation API endpoint directly.
This sends a request to the running EchoForge server and saves the generated audio.
"""

import os
import sys
import requests
import json
import argparse
import time
import subprocess
import re
from pathlib import Path

OUTPUT_DIR = "/tmp/echoforge/voices/api_test"
PORT_FILE = os.path.expanduser("~/.echoforge_port")

def save_port(port):
    """Save the detected port to a file for future use."""
    try:
        with open(PORT_FILE, "w") as f:
            f.write(str(port))
        print(f"Saved port {port} to {PORT_FILE}")
    except Exception as e:
        print(f"Warning: Could not save port to file: {e}")

def load_saved_port():
    """Load the previously saved port from file."""
    try:
        port_file = os.path.expanduser("~/.echoforge_port")
        if os.path.exists(port_file):
            with open(port_file, "r") as f:
                port = int(f.read().strip())
                print(f"Using saved port {port} from {port_file}")
                return port
    except Exception as e:
        print(f"Warning: Could not load saved port: {e}")
    return None

def find_server_port():
    """
    Find the port that the EchoForge server is running on.
    First tries to read from the port file, then falls back to other methods.
    
    Returns:
        The port number or None if not found
    """
    # First try to load from saved file
    saved_port = load_saved_port()
    if saved_port:
        return saved_port
    
    # If we couldn't find the port, try common ports
    print("Port file not found. Trying common ports...")
    common_ports = [8765, 8780, 8000, 5000]
    for port in common_ports:
        try:
            # Try to connect to the port
            response = requests.get(f"http://localhost:{port}/api/health", timeout=1)
            if response.status_code == 200:
                print(f"Found EchoForge server on port {port}")
                save_port(port)
                return port
        except:
            pass
    
    print("Could not determine server port. Please specify with --port.")
    return None

def get_server_url(provided_url=None):
    """
    Get the server URL, either from the provided URL or by detecting the port.
    
    Args:
        provided_url: The URL provided by the user, if any
    
    Returns:
        The complete server URL or None if not found
    """
    if provided_url and provided_url != "auto":
        return provided_url
    
    # Auto-detect the port
    port = find_server_port()
    if not port:
        print("Could not determine server port. Please specify with --port.")
        return None
    
    return f"http://localhost:{port}"

def test_voice_api(text="hello", server_url="auto"):
    """
    Test the voice generation API by sending a direct request.
    
    Args:
        text: Text to generate speech for
        server_url: URL of the EchoForge server, or "auto" to detect
    
    Returns:
        Path to the saved audio file or None if failed
    """
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Get the actual server URL
    full_server_url = get_server_url(server_url)
    if not full_server_url:
        print("Error: Could not determine server URL. Please specify with --server or --port.")
        return None
    
    # Create a timestamp for the filename
    timestamp = int(time.time())
    output_file = os.path.join(OUTPUT_DIR, f"api_test_{timestamp}.wav")
    
    # Prepare the request data
    api_url = f"{full_server_url}/api/voice/generate"
    data = {
        "text": text,
        "speaker_id": 1,
        "temperature": 0.7,
        "top_k": 50,
        "device": "auto"
    }
    
    print(f"Sending request to {api_url} with text: '{text}'")
    
    # Send the request
    try:
        response = requests.post(api_url, json=data, timeout=60)
        
        # Check for success
        if response.status_code == 200:
            print(f"Request successful: {response.status_code}")
            
            # Parse the response
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Check if we got a voice URL
            if "url" in result:
                voice_url = result["url"]
                print(f"Voice URL: {voice_url}")
                
                # Download the voice file
                audio_response = requests.get(f"{full_server_url}{voice_url}", timeout=30)
                if audio_response.status_code == 200:
                    # Save the audio file
                    with open(output_file, "wb") as f:
                        f.write(audio_response.content)
                    print(f"Voice saved to: {output_file}")
                    return output_file
                else:
                    print(f"Error downloading voice file: {audio_response.status_code}")
            else:
                print("No voice URL found in response")
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(f"Response content: {response.text}")
    
    except Exception as e:
        print(f"Error: {e}")
    
    return None

def main():
    """Main function to parse arguments and run the test."""
    parser = argparse.ArgumentParser(description="Test the EchoForge voice generation API")
    parser.add_argument("text", nargs="?", default="hello", help="Text to generate speech for")
    parser.add_argument("--server", default="auto", help="Server URL (default: auto-detect)")
    parser.add_argument("--port", type=int, help="Specify server port directly")
    
    args = parser.parse_args()
    
    # If port is specified, save it and use it
    if args.port:
        save_port(args.port)
        server_url = f"http://localhost:{args.port}"
    else:
        server_url = args.server
    
    # Run the test
    output_file = test_voice_api(args.text, server_url)
    
    if output_file:
        print("\nSuccess! To play the audio:")
        print(f"aplay {output_file}")
        return 0
    else:
        print("\nFailed to generate voice.")
        print("Make sure the EchoForge server is running and specify the correct port with --port.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 