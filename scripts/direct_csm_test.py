#!/usr/bin/env python3
"""
Direct CSM Test Script

This script directly uses the CSM (Conversational Speech Model) to generate voice output,
bypassing the EchoForge API layer. It's useful for testing the CSM model in isolation
and diagnosing issues with voice generation.

Features:
- Automatically finds the CSM model checkpoint
- Generates speech using the CSM model directly
- Saves the output to the EchoForge voices directory
- Creates a symlink for easy access to the latest generated file
- Works with the EchoForge voice browser

Usage:
    ./scripts/direct_csm_test.py [text]

    If no text is provided, a default test message will be used.

Example:
    ./scripts/direct_csm_test.py "Hello, this is a test of the CSM model."

Requirements:
    - PyTorch
    - TorchAudio
    - CSM model code in /home/tdeshane/tts_poc/voice_poc/csm
    - CSM model checkpoint (automatically located)

Notes:
    This script is part of the EchoForge project and is intended for
    testing and development purposes. It bypasses the normal API flow
    to directly test the underlying CSM model.
"""

import os
import sys
import torch
import torchaudio
import time
from datetime import datetime

# Add the CSM directory to the path
CSM_PATH = "/home/tdeshane/tts_poc/voice_poc/csm"
sys.path.append(CSM_PATH)

# Output directory
OUTPUT_DIR = "/tmp/echoforge/voices/generated"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    """Main function to generate speech using the CSM model directly."""
    print("Loading CSM modules...")
    try:
        from generator import load_csm_1b
    except ImportError as e:
        print(f"Error importing CSM modules: {e}")
        print(f"Make sure the CSM code is available at: {CSM_PATH}")
        sys.exit(1)
    
    # Find the model checkpoint
    print("Looking for model checkpoint...")
    model_path = None
    
    # Try the default location
    default_path = os.path.join(CSM_PATH, "ckpt.pt")
    if os.path.exists(default_path):
        model_path = default_path
    
    # Try the Hugging Face cache
    if not model_path:
        hf_cache = os.path.expanduser("~/.cache/huggingface/hub")
        for root, dirs, files in os.walk(hf_cache):
            if "ckpt.pt" in files:
                model_path = os.path.join(root, "ckpt.pt")
                break
    
    if not model_path:
        print("Could not find model checkpoint. Please specify the path.")
        sys.exit(1)
    
    print(f"Found model checkpoint: {model_path}")
    
    # Determine device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Load the model
    print("Loading CSM model...")
    try:
        generator = load_csm_1b(model_path, device)
        print("Model loaded successfully")
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)
    
    # Get text from command line or use default
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = "This is a direct test of the CSM model. The voice should be clear and natural sounding."
    
    print(f"Generating speech for text: '{text}'")
    
    start_time = time.time()
    try:
        audio = generator.generate(
            text=text,
            speaker=0,
            context=[],
            temperature=0.9,
            topk=50
        )
        generation_time = time.time() - start_time
        print(f"Speech generated in {generation_time:.2f} seconds")
    except Exception as e:
        print(f"Error generating speech: {e}")
        sys.exit(1)
    
    # Save the audio
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(OUTPUT_DIR, f"direct_csm_test_{timestamp}.wav")
    
    try:
        print(f"Saving audio to {output_path}")
        torchaudio.save(output_path, audio.unsqueeze(0).cpu(), generator.sample_rate)
        print(f"Audio saved successfully")
        print(f"File size: {os.path.getsize(output_path)} bytes")
    except Exception as e:
        print(f"Error saving audio: {e}")
        sys.exit(1)
    
    # Create a symlink for the latest file
    latest_path = os.path.join(OUTPUT_DIR, "latest_direct_csm.wav")
    try:
        # Remove existing symlink if it exists
        if os.path.exists(latest_path):
            os.remove(latest_path)
        
        # Create the symlink
        os.symlink(output_path, latest_path)
        print(f"Created symlink: {latest_path} -> {output_path}")
    except Exception as e:
        print(f"Error creating symlink: {e}")
    
    print("\nTo check the audio in the browser, visit:")
    print("http://localhost:8765/api/browser")
    print("\nTo play the audio directly:")
    print(f"aplay {output_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 