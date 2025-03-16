#!/usr/bin/env python3
"""
Simple test script for direct voice generation.
Tests with a single word and provides information about the output.
This script directly uses the CSM generator module from voice_poc.
"""

import os
import sys
import logging
import subprocess
import time
import glob
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice_test")

# Default paths
VOICE_POC_PATH = "/home/tdeshane/movie_maker/voice_poc"
OUTPUT_DIR = "/tmp/echoforge/voices/test"

def test_voice_generation(text="hello", device="cpu"):
    """
    Test voice generation with a single word.
    
    Args:
        text: Text to generate speech for (default: "hello")
        device: Device to use for generation (cpu or cuda)
    """
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Create a unique filename
    timestamp = int(time.time())
    output_filename = f"test_voice_{timestamp}.wav"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    logger.info(f"Testing voice generation for text: '{text}'")
    logger.info(f"Output will be saved to: {output_path}")
    
    # Create a simple Python script that directly uses the Generator class
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
        
        return False
    
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
    else:
        # Look for any generated files
        logger.warning(f"Expected output file not found: {output_path}")
        
        # Find the generated file
        generated_files = glob.glob(os.path.join(OUTPUT_DIR, "*.wav"))
        newest_file = None
        newest_time = 0
        
        for file_path in generated_files:
            file_mtime = os.path.getmtime(file_path)
            if file_mtime > newest_time:
                newest_time = file_mtime
                newest_file = file_path
        
        if not newest_file:
            logger.error("No output file found")
            return False
        
        output_path = newest_file
        logger.info(f"Using alternate output file: {output_path}")
    
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

if __name__ == "__main__":
    # Get text from command line arguments or use default
    text = sys.argv[1] if len(sys.argv) > 1 else "hello"
    
    # Get device from command line arguments or use default
    device = sys.argv[2] if len(sys.argv) > 2 else "cpu"
    
    output_file = test_voice_generation(text, device)
    
    if output_file:
        print(f"\nSuccess! Generated file: {output_file}")
        print(f"To play the audio: aplay {output_file}")
    else:
        print("\nFailed to generate voice.")
        sys.exit(1) 