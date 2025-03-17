#!/usr/bin/env python3
"""
Direct CSM Voice Generation Test

This script directly calls the CSM model in the movie_maker/voice_poc directory.
It bypasses the adapter layer and directly uses the Generator class.
"""

import os
import sys
import logging
import time
import shutil
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("direct_csm_test")

# Paths
MOVIE_MAKER_PATH = "/home/tdeshane/movie_maker"
VOICE_POC_PATH = os.path.join(MOVIE_MAKER_PATH, "voice_poc")
ECHOFORGE_OUTPUT_DIR = "/tmp/echoforge/voices/generated"

def generate_voice_direct(text, device="cuda"):
    """
    Generate a voice file by directly calling the CSM model.
    
    Args:
        text: The text to convert to speech
        device: The device to use (cuda or cpu)
        
    Returns:
        The path to the generated voice file
    """
    # Ensure output directory exists
    os.makedirs(ECHOFORGE_OUTPUT_DIR, exist_ok=True)
    
    # Create a unique filename
    timestamp = int(time.time())
    filename = f"voice_{timestamp}_{text[:10].replace(' ', '_')}.wav"
    output_path = os.path.join(ECHOFORGE_OUTPUT_DIR, filename)
    
    logger.info(f"Generating voice for text: '{text}'")
    logger.info(f"Using device: {device}")
    logger.info(f"Output will be saved to: {output_path}")
    
    # Create a temporary Python script that directly uses the Generator class
    temp_script = os.path.join(ECHOFORGE_OUTPUT_DIR, "temp_generator.py")
    
    with open(temp_script, "w") as f:
        f.write(f"""
#!/usr/bin/env python3
# Temporary direct voice generation script
import os
import sys
import torch
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("direct_voice_generator")

# Add the voice_poc path to sys.path
voice_poc_path = "{VOICE_POC_PATH}"
sys.path.insert(0, voice_poc_path)

try:
    # Import the Generator class
    from csm.generator import Generator
    logger.info("Successfully imported Generator")
    
    # Initialize the generator
    logger.info(f"Initializing generator with device: {device}")
    generator = Generator(device="{device}")
    logger.info("Generator initialized")
    
    # Generate speech for the text
    logger.info(f"Generating speech for: '{text}'")
    start_time = time.time()
    audio = generator.generate_audio_for_text("{text}")
    end_time = time.time()
    logger.info(f"Generation completed in {end_time - start_time:.2f} seconds")
    
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
    
    # Make the script executable
    os.chmod(temp_script, 0o755)
    
    # Run the script using the movie_maker virtual environment
    cmd = [
        "bash", "-c", 
        f"cd {VOICE_POC_PATH} && source venv/bin/activate && python {temp_script}"
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for the process to complete
    stdout, stderr = process.communicate()
    
    # Log the output
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
        
        return output_path
    else:
        logger.error(f"Output file not found: {output_path}")
        return None

if __name__ == "__main__":
    # Get the text from the command line
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Hello world"
    
    # Generate the voice
    output_path = generate_voice_direct(text)
    
    if output_path:
        print(f"\nSuccess! Generated voice file at: {output_path}")
        print(f"To play the audio: aplay {output_path}")
        print(f"View in browser: http://localhost:8765/api/browser")
    else:
        print("\nFailed to generate voice")
        sys.exit(1) 