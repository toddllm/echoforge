#!/usr/bin/env python3
"""
Test script for CSM voice generation.

This script uses the CSM adapter from the TTS POC to generate a voice file.
It saves the output to the EchoForge generated directory so it will appear in the browser.
"""

import os
import sys
import logging
import time
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("csm_voice_test")

# Add the TTS POC directory to the path
TTS_POC_PATH = "/home/tdeshane/tts_poc"
sys.path.append(TTS_POC_PATH)

# Output directory for EchoForge
ECHOFORGE_OUTPUT_DIR = "/tmp/echoforge/voices/generated"

def generate_voice(text, device="cuda"):
    """
    Generate a voice file using the CSM adapter.
    
    Args:
        text: The text to convert to speech
        device: The device to use (cuda or cpu)
        
    Returns:
        The path to the generated voice file
    """
    try:
        # Import the CSM adapter
        from utils.csm_adapter import CSMModelAdapter
        
        logger.info(f"Generating voice for text: '{text}'")
        logger.info(f"Using device: {device}")
        
        # Create the adapter
        adapter = CSMModelAdapter()
        
        # Generate the speech
        output_path = adapter.generate_speech(text, device=device)
        
        if not output_path:
            logger.error("Failed to generate speech")
            return None
        
        logger.info(f"Generated speech at: {output_path}")
        
        # Copy the file to the EchoForge output directory
        os.makedirs(ECHOFORGE_OUTPUT_DIR, exist_ok=True)
        
        # Create a unique filename
        timestamp = int(time.time())
        filename = f"voice_{timestamp}_{text[:10].replace(' ', '_')}.wav"
        echoforge_path = os.path.join(ECHOFORGE_OUTPUT_DIR, filename)
        
        # Copy the file
        shutil.copy2(output_path, echoforge_path)
        logger.info(f"Copied to EchoForge output directory: {echoforge_path}")
        
        return echoforge_path
    
    except Exception as e:
        logger.exception(f"Error generating voice: {e}")
        return None

if __name__ == "__main__":
    # Get the text from the command line
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Hello world"
    
    # Generate the voice
    output_path = generate_voice(text)
    
    if output_path:
        print(f"\nSuccess! Generated voice file at: {output_path}")
        print(f"To play the audio: aplay {output_path}")
        print(f"View in browser: http://localhost:8765/api/browser")
    else:
        print("\nFailed to generate voice")
        sys.exit(1) 