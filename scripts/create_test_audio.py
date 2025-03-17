#!/usr/bin/env python3
"""
Create a test audio file for the voice browser
"""

import os
import numpy as np
from scipy.io import wavfile
import time
from datetime import datetime

# Create a simple sine wave audio sample
sample_rate = 24000
duration = 3  # seconds
t = np.linspace(0, duration, int(sample_rate * duration))

# Generate a 440 Hz sine wave (A4 note)
audio = np.sin(2 * np.pi * 440 * t)

# Add a second tone to make it more interesting (A5 note)
audio += 0.5 * np.sin(2 * np.pi * 880 * t)

# Add a third tone (E5 note)
audio += 0.3 * np.sin(2 * np.pi * 659.25 * t)

# Create a simple envelope to avoid clicks
envelope = np.ones_like(audio)
attack_samples = int(0.1 * sample_rate)  # 100ms attack
release_samples = int(0.1 * sample_rate)  # 100ms release
envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
envelope[-release_samples:] = np.linspace(1, 0, release_samples)
audio = audio * envelope

# Normalize
audio = audio / np.max(np.abs(audio))

# Convert to 16-bit PCM
audio = (audio * 32767).astype(np.int16)

# Create output directory
output_dir = "/tmp/echoforge/voices/generated"
os.makedirs(output_dir, exist_ok=True)

# Generate a unique filename with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = os.path.join(output_dir, f"test_sine_wave_{timestamp}.wav")

# Save the audio file
print(f"Saving test audio to {output_path}")
wavfile.write(output_path, sample_rate, audio)
print(f"Saved test audio file: {output_path}")
print(f"File size: {os.path.getsize(output_path)} bytes")

# Create a symlink for the latest file
latest_path = os.path.join(output_dir, "latest_test.wav")
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