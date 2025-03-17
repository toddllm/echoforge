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
import shutil
from pathlib import Path
from datetime import datetime
import hashlib

# Standardized directory structure
ECHOFORGE_ROOT = "/tmp/echoforge"
VOICES_DIR = os.path.join(ECHOFORGE_ROOT, "voices")
GENERATED_DIR = os.path.join(VOICES_DIR, "generated")
TEMP_DIR = os.path.join(VOICES_DIR, "temp")
CACHE_DIR = os.path.join(VOICES_DIR, "cache")
LOGS_DIR = os.path.join(VOICES_DIR, "logs")
PORT_FILE = os.path.expanduser("~/.echoforge_port")

def ensure_directories():
    """Create the standardized directory structure if it doesn't exist."""
    for directory in [GENERATED_DIR, TEMP_DIR, CACHE_DIR, LOGS_DIR]:
        os.makedirs(directory, exist_ok=True)
        # Verify the directory was created and is writable
        if not os.path.exists(directory):
            print(f"Error: Failed to create directory {directory}")
            return False
        if not os.access(directory, os.W_OK):
            print(f"Error: Directory {directory} is not writable")
            return False
    
    print(f"Directory structure verified at {ECHOFORGE_ROOT}")
    return True

def log_file_operation(operation, file_path, status, details=None):
    """Log file operations for debugging."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = os.path.join(LOGS_DIR, "file_operations.log")
    
    message = f"{timestamp} | {operation} | {file_path} | {status}"
    if details:
        message += f" | {details}"
    
    try:
        with open(log_file, "a") as f:
            f.write(message + "\n")
    except Exception as e:
        print(f"Warning: Could not write to log file: {e}")
    
    # Also print to console
    print(message)

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
    common_ports = [8765, 8779, 8780, 8000, 5000]
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

def generate_file_path(text, task_id=None, is_temp=False):
    """
    Generate a standardized file path for voice output.
    
    Args:
        text: The text being converted to speech
        task_id: The task ID from the API (if available)
        is_temp: Whether this is a temporary file
    
    Returns:
        Path to the file
    """
    # Create a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create a hash of the text for uniqueness
    text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
    
    # Determine the base filename
    if task_id:
        filename = f"voice_{timestamp}_{task_id}_{text_hash}.wav"
    else:
        filename = f"voice_{timestamp}_{text_hash}.wav"
    
    # Determine the directory
    if is_temp:
        directory = TEMP_DIR
    else:
        directory = GENERATED_DIR
    
    # Return the full path
    return os.path.join(directory, filename)

def verify_file_exists(file_path, operation="check"):
    """
    Verify that a file exists and is readable.
    
    Args:
        file_path: Path to the file to check
        operation: The operation being performed (for logging)
    
    Returns:
        True if the file exists and is readable, False otherwise
    """
    if not os.path.exists(file_path):
        log_file_operation(operation, file_path, "FAILED", "File does not exist")
        return False
    
    if not os.path.isfile(file_path):
        log_file_operation(operation, file_path, "FAILED", "Path exists but is not a file")
        return False
    
    if not os.access(file_path, os.R_OK):
        log_file_operation(operation, file_path, "FAILED", "File exists but is not readable")
        return False
    
    # File exists and is readable
    log_file_operation(operation, file_path, "SUCCESS", "File exists and is readable")
    return True

def test_voice_api(text="hello", server_url="auto", args=None):
    """
    Test the voice generation API by sending a direct request.
    
    Args:
        text: Text to generate speech for
        server_url: URL of the EchoForge server, or "auto" to detect
        args: Command line arguments
    
    Returns:
        Path to the saved audio file or None if failed
    """
    # Use default args if not provided
    if args is None:
        class DefaultArgs:
            temperature = 0.7
            top_k = 50
            device = "cuda"
        args = DefaultArgs()
        
    # Ensure directories exist
    if not ensure_directories():
        print("Error: Failed to create or verify required directories")
        return None
    
    # Get the actual server URL
    full_server_url = get_server_url(server_url)
    if not full_server_url:
        print("Error: Could not determine server URL. Please specify with --server or --port.")
        return None
    
    # Prepare the request data
    api_url = f"{full_server_url}/api/generate"
    data = {
        "text": text,
        "speaker_id": 1,
        "temperature": args.temperature,
        "top_k": args.top_k,
        "device": args.device,
        "style": "default"
    }
    
    print(f"Sending request to {api_url} with text: '{text}'")
    print(f"Parameters: temperature={args.temperature}, top_k={args.top_k}, device={args.device}")
    
    # Send the request
    try:
        response = requests.post(api_url, json=data, timeout=60)
        
        # Check for success
        if response.status_code == 200:
            print(f"Request successful: {response.status_code}")
            
            # Parse the response
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Check if we got a task ID
            if "task_id" in result:
                task_id = result["task_id"]
                print(f"Task ID: {task_id}")
                
                # Create a temporary file path for this task
                temp_file_path = generate_file_path(text, task_id, is_temp=True)
                final_file_path = generate_file_path(text, task_id, is_temp=False)
                
                # Poll for task completion
                task_url = f"{full_server_url}/api/tasks/{task_id}"
                print(f"Polling task status at: {task_url}")
                
                max_attempts = 30
                for attempt in range(max_attempts):
                    print(f"Checking task status (attempt {attempt+1}/{max_attempts})...")
                    
                    try:
                        # Use a longer timeout for task polling
                        task_response = requests.get(task_url, timeout=30)
                        
                        if task_response.status_code == 200:
                            task_result = task_response.json()
                            print(f"Task status: {task_result.get('status', 'unknown')}")
                            
                            # Check if task is completed
                            if task_result.get("status") == "completed":
                                # Get the file URL
                                if "result" in task_result and "file_url" in task_result["result"]:
                                    voice_url = task_result["result"]["file_url"]
                                    print(f"Voice URL: {voice_url}")
                                    
                                    # Download the voice file
                                    audio_response = requests.get(f"{full_server_url}{voice_url}", timeout=30)
                                    if audio_response.status_code == 200:
                                        # Save the audio file to temp location first
                                        with open(temp_file_path, "wb") as f:
                                            f.write(audio_response.content)
                                        
                                        log_file_operation("download", temp_file_path, "SUCCESS", 
                                                          f"Downloaded from {voice_url}")
                                        
                                        # Verify the file was saved correctly
                                        if verify_file_exists(temp_file_path, "download_verify"):
                                            # Move to final location
                                            shutil.copy2(temp_file_path, final_file_path)
                                            log_file_operation("copy", final_file_path, "SUCCESS", 
                                                              f"Copied from {temp_file_path}")
                                            
                                            # Verify the final file
                                            if verify_file_exists(final_file_path, "final_verify"):
                                                print(f"Voice saved to: {final_file_path}")
                                                
                                                # Create symlinks for compatibility with other systems
                                                symlink_path = os.path.join(CACHE_DIR, f"latest_{task_id}.wav")
                                                try:
                                                    # Remove existing symlink if it exists
                                                    if os.path.exists(symlink_path):
                                                        os.remove(symlink_path)
                                                    
                                                    # Create the symlink
                                                    os.symlink(final_file_path, symlink_path)
                                                    log_file_operation("symlink", symlink_path, "SUCCESS", 
                                                                      f"Linked to {final_file_path}")
                                                except Exception as e:
                                                    log_file_operation("symlink", symlink_path, "FAILED", str(e))
                                                
                                                return final_file_path
                                            else:
                                                print(f"Error: Final file verification failed")
                                        else:
                                            print(f"Error: Temp file verification failed")
                                    else:
                                        print(f"Error downloading voice file: {audio_response.status_code}")
                                        log_file_operation("download", temp_file_path, "FAILED", 
                                                          f"HTTP {audio_response.status_code}")
                                        break
                                else:
                                    print("No file URL found in completed task")
                                    log_file_operation("task_complete", "N/A", "FAILED", "No file URL in response")
                                    break
                            elif task_result.get("status") == "failed":
                                error_msg = task_result.get('error', 'Unknown error')
                                print(f"Task failed: {error_msg}")
                                log_file_operation("task", task_id, "FAILED", error_msg)
                                break
                            
                            # If task is still processing, wait and try again
                            if task_result.get("status") == "processing":
                                # Wait longer between checks (5 seconds)
                                print(f"Task still processing, waiting 5 seconds...")
                                time.sleep(5)
                            else:
                                # Unknown status
                                unknown_status = task_result.get('status')
                                print(f"Unknown task status: {unknown_status}")
                                log_file_operation("task", task_id, "UNKNOWN", f"Status: {unknown_status}")
                                break
                        else:
                            print(f"Error checking task status: {task_response.status_code}")
                            print(f"Response: {task_response.text}")
                            log_file_operation("task_check", task_id, "FAILED", 
                                              f"HTTP {task_response.status_code}")
                            break
                    except Exception as e:
                        print(f"Error polling task: {e}")
                        log_file_operation("task_poll", task_id, "ERROR", str(e))
                        # Try again after a delay
                        print(f"Retrying after 5 seconds...")
                        time.sleep(5)
                        continue
                
                print("Exceeded maximum polling attempts or task failed")
                log_file_operation("task_complete", task_id, "FAILED", "Max attempts exceeded")
            else:
                print("No task ID found in response")
                log_file_operation("api_request", api_url, "FAILED", "No task ID in response")
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(f"Response content: {response.text}")
            log_file_operation("api_request", api_url, "FAILED", f"HTTP {response.status_code}")
    
    except Exception as e:
        print(f"Error: {e}")
        log_file_operation("api_request", api_url, "ERROR", str(e))
    
    return None

def main():
    """Main function to parse arguments and run the test."""
    parser = argparse.ArgumentParser(description="Test the EchoForge voice generation API")
    parser.add_argument("text", nargs="?", default="hello", help="Text to generate speech for")
    parser.add_argument("--server", default="auto", help="Server URL (default: auto-detect)")
    parser.add_argument("--port", type=int, help="Specify server port directly")
    parser.add_argument("--verify-dirs", action="store_true", help="Verify directory structure only")
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"], help="Device to use for generation")
    parser.add_argument("--temperature", type=float, default=0.7, help="Temperature for sampling (higher = more diverse)")
    parser.add_argument("--top-k", type=int, default=50, help="Number of highest probability tokens to consider")
    
    args = parser.parse_args()
    
    # If only verifying directories, do that and exit
    if args.verify_dirs:
        if ensure_directories():
            print("Directory structure verified successfully")
            return 0
        else:
            print("Directory structure verification failed")
            return 1
    
    # If port is specified, save it and use it
    if args.port:
        save_port(args.port)
        server_url = f"http://localhost:{args.port}"
    else:
        server_url = args.server
    
    # Run the test
    output_file = test_voice_api(args.text, server_url, args)
    
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