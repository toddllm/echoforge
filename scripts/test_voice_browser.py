#!/usr/bin/env python3
"""
Test script for voice generation that saves to the browser-visible directory.
This script generates a simple voice file using the GPU and saves it to the
directory where the voice browser can find it.
"""

import os
import sys
import logging
import subprocess
import time
import datetime
import uuid
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice_browser_test")

# Default paths
VOICE_POC_PATH = "/home/tdeshane/movie_maker/voice_poc"
# This is the directory that the browser looks for voice files
OUTPUT_DIR = "/tmp/echoforge/voices/generated"

def generate_voice_for_browser(text="Hello world", device="cuda"):
    """
    Generate a voice file and save it to the browser-visible directory.
    
    Args:
        text: Text to generate speech for (default: "Hello world")
        device: Device to use for generation (cuda or cpu)
    """
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Create a unique filename with timestamp and UUID
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4()
    output_filename = f"voice_{timestamp}_{unique_id}_{text[:10].replace(' ', '_')}.wav"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    logger.info(f"Generating voice for text: '{text}'")
    logger.info(f"Using device: {device}")
    logger.info(f"Output will be saved to: {output_path}")
    
    # Create a temporary Python script that directly uses the Generator class
    temp_script = os.path.join(OUTPUT_DIR, "temp_generator.py")
    
    with open(temp_script, "w") as f:
        f.write(f"""
# Temporary direct voice generation script
import os
import sys
import torch
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("direct_voice_generator")

# Add the voice_poc path to sys.path
voice_poc_path = "{VOICE_POC_PATH}"
sys.path.insert(0, voice_poc_path)

try:
    # Import the Generator class from CSM
    from csm.generator import Generator
    logger.info("Successfully imported CSM Generator")
    
    # Initialize the generator
    generator = Generator(device="{device}")
    logger.info(f"Initialized generator with device: {device}")
    
    # Generate speech for the text
    logger.info(f"Generating speech for: '{text}'")
    audio = generator.generate_audio_for_text("{text}")
    
    # Save the audio
    output_path = "{output_path}"
    generator.save_audio(audio, output_path)
    logger.info(f"Saved audio to: {output_path}")
    print(f"OUTPUT_FILE: {output_path}")
    sys.exit(0)
except Exception as e:
    logger.error(f"Error: {{e}}")
    print(f"ERROR: {{e}}")
    sys.exit(1)
""")
    
    logger.info(f"Created temporary generator script: {temp_script}")
    
    # Start time for measuring performance
    start_time = time.time()
    
    # Run the script
    cmd = [sys.executable, temp_script]
    logger.info(f"Running command: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=VOICE_POC_PATH
    )
    
    # Wait for the process to complete
    stdout, stderr = process.communicate()
    
    # End time
    end_time = time.time()
    duration = end_time - start_time
    
    # Check the result
    if process.returncode != 0:
        logger.error(f"Voice generation failed with return code: {process.returncode}")
        logger.error(f"STDOUT: {stdout}")
        logger.error(f"STDERR: {stderr}")
        
        # Clean up
        try:
            os.unlink(temp_script)
        except:
            pass
        
        return None
    
    logger.info(f"Voice generation completed in {duration:.2f} seconds")
    
    # Log output
    logger.info(f"STDOUT: {stdout}")
    if stderr:
        logger.info(f"STDERR: {stderr}")
    
    # Clean up the temporary script
    try:
        os.unlink(temp_script)
    except:
        logger.warning(f"Could not remove temporary script: {temp_script}")
    
    # Check if the file was created
    if os.path.exists(output_path):
        logger.info(f"Found output file: {output_path}")
        
        # Get file information
        file_size = os.path.getsize(output_path)
        logger.info(f"File size: {file_size} bytes ({file_size/1024:.2f} KB)")
        
        # Get audio information using ffprobe
        try:
            ffprobe_cmd = [
                "ffprobe",
                "-v", "error",
                "-show_format",
                "-show_streams",
                output_path
            ]
            
            ffprobe_output = subprocess.check_output(ffprobe_cmd, text=True)
            logger.info(f"Audio information:\n{ffprobe_output}")
        except Exception as e:
            logger.error(f"Error getting audio info: {e}")
        
        return output_path
    else:
        logger.error(f"Expected output file not found: {output_path}")
        return None

if __name__ == "__main__":
    # Get text from command line arguments or use default
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Hello world"
    
    # Use CUDA by default for this test
    device = "cuda"
    
    output_file = generate_voice_for_browser(text, device)
    
    if output_file:
        print(f"\nSuccess! Generated file: {output_file}")
        print(f"To play the audio: aplay {output_file}")
        print(f"View in browser: http://localhost:8766/api/browser")
    else:
        print("\nFailed to generate voice.")
        sys.exit(1) 