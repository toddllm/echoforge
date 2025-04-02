#!/usr/bin/env python3
"""
Setup Voice Files for EchoForge

This script generates voice sample files for the EchoForge application
and places them in the correct directory structure for the voice
generation system to use. It creates a set of high-quality placeholder
audio files that can be used as voice models.

Usage:
    python setup_voices.py [--force]

Options:
    --force    Overwrite existing voice files if they exist

The script will:
1. Create the necessary directory structure
2. Generate sample voice files with different characteristics
3. Place them in the correct locations for EchoForge to use

These voice files are used by the EchoForge voice generation system
to provide a starting point for voice synthesis.
"""

import os
import sys
import argparse
import shutil
import random
import wave
import struct
import numpy as np
from pathlib import Path

# Voice configurations with detailed parameters
VOICE_CONFIGS = [
    {
        "id": 1,
        "name": "Commander Sterling",
        "gender": "male",
        "description": "Deep authoritative voice with confident tone",
        "base_freq": 110.0,  # Lower frequency for male voice
        "formant_shift": 0.9,  # Lower formants for male
        "duration": 4.0,
        "character_traits": "confident, commanding, authoritative"
    },
    {
        "id": 2,
        "name": "Dr. Elise Jensen",
        "gender": "female",
        "description": "Clear, articulate voice with professional tone",
        "base_freq": 220.0,  # Higher frequency for female voice
        "formant_shift": 1.1,  # Higher formants for female
        "duration": 3.5,
        "character_traits": "intelligent, precise, professional"
    },
    {
        "id": 3,
        "name": "James Fletcher",
        "gender": "male",
        "description": "Warm, friendly voice with natural cadence",
        "base_freq": 130.0,
        "formant_shift": 0.95,
        "duration": 5.0,
        "character_traits": "warm, friendly, approachable"
    },
    {
        "id": 4,
        "name": "Sophia Chen",
        "gender": "female",
        "description": "Energetic voice with varied intonation",
        "base_freq": 240.0,
        "formant_shift": 1.15,
        "duration": 4.2,
        "character_traits": "energetic, expressive, dynamic"
    },
    {
        "id": 5,
        "name": "Morgan Riley",
        "gender": "neutral",
        "description": "Balanced, neutral voice with moderate tone",
        "base_freq": 165.0,  # Middle frequency for neutral voice
        "formant_shift": 1.0,  # Neutral formants
        "duration": 3.8,
        "character_traits": "balanced, neutral, versatile"
    }
]

def create_voice_audio(filename, voice_config, sample_rate=22050):
    """
    Create a voice audio file with characteristics based on voice_config.
    
    Args:
        filename: Output filename
        voice_config: Dictionary with voice configuration parameters
        sample_rate: Sample rate in Hz
    """
    # Extract parameters from voice config
    base_freq = voice_config["base_freq"]
    formant_shift = voice_config["formant_shift"]
    duration = voice_config["duration"]
    
    # Parameters
    amplitude = 24000  # Slightly below 16-bit max to avoid clipping
    num_samples = int(duration * sample_rate)
    
    # Generate time array
    t = np.linspace(0, duration, num_samples)
    
    # Create fundamental frequency with slight variation
    freq_mod = 1.0 + 0.01 * np.sin(2 * np.pi * 0.5 * t)
    fundamental = amplitude * 0.5 * np.sin(2 * np.pi * base_freq * freq_mod * t)
    
    # Add harmonics for richer voice quality
    audio_data = fundamental.copy()
    
    # Add several harmonics with decreasing amplitude
    for harmonic in range(2, 6):
        harmonic_amp = amplitude * 0.5 / harmonic
        formant_freq = base_freq * harmonic * formant_shift
        audio_data += harmonic_amp * np.sin(2 * np.pi * formant_freq * t)
    
    # Add some noise for breathiness
    noise = np.random.normal(0, amplitude * 0.05, num_samples)
    audio_data += noise
    
    # Apply a more natural envelope
    envelope = np.ones(num_samples)
    attack = int(0.1 * sample_rate)
    release = int(0.2 * sample_rate)
    decay = int(0.05 * sample_rate)
    sustain_level = 0.8
    
    # Attack phase
    envelope[:attack] = np.linspace(0, 1, attack)
    # Decay phase
    envelope[attack:attack+decay] = np.linspace(1, sustain_level, decay)
    # Sustain phase is already set to ones, adjusted by sustain_level
    envelope[attack+decay:-release] = sustain_level
    # Release phase
    envelope[-release:] = np.linspace(sustain_level, 0, release)
    
    # Add some natural tremolo (slight amplitude variation)
    tremolo = 1.0 + 0.05 * np.sin(2 * np.pi * 5 * t)
    envelope = envelope * tremolo
    
    audio_data = audio_data * envelope
    
    # Add subtle vibrato (frequency variation) for naturalness
    vibrato_rate = 5.0  # Hz
    vibrato_depth = 0.02  # 2% frequency variation
    
    # Ensure we stay within 16-bit range
    audio_data = np.clip(audio_data, -32767, 32767).astype(np.int16)
    
    # Create WAV file
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16 bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    print(f"Created voice file: {filename}")
    return filename

def copy_file_if_exists(src, dest):
    """Copy a file if it exists, otherwise return False."""
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)
        print(f"Copied: {src} -> {dest}")
        return True
    return False

def setup_directory_structure():
    """Create the necessary directory structure for voice files."""
    # Define the main directories needed
    directories = [
        "static/voices/creative",
        "static/voices/standard",
        "static/images",
        "static/samples"
    ]
    
    # Create directories
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Ensured directory exists: {directory}")

def create_voice_metadata_file(voice_configs, output_path):
    """Create a metadata file with information about available voices."""
    with open(output_path, 'w') as f:
        f.write("# EchoForge Voice Metadata\n")
        f.write("# This file contains information about available voices\n\n")
        
        for voice in voice_configs:
            f.write(f"## Voice ID: {voice['id']}\n")
            f.write(f"Name: {voice['name']}\n")
            f.write(f"Gender: {voice['gender']}\n")
            f.write(f"Description: {voice['description']}\n")
            f.write(f"Character Traits: {voice['character_traits']}\n")
            f.write(f"Base Frequency: {voice['base_freq']} Hz\n")
            f.write(f"Duration: {voice['duration']} seconds\n\n")
    
    print(f"Created voice metadata file: {output_path}")

def create_default_sample_texts():
    """Create default sample text file for voice generation."""
    sample_texts = {
        "greetings": [
            "Hello, it's nice to meet you. Welcome to EchoForge voice generation system.",
            "Greetings and welcome! I'm excited to help you explore the world of voice synthesis.",
            "Hi there! I'm a synthesized voice created by EchoForge. How can I assist you today?"
        ],
        "information": [
            "EchoForge is an advanced voice generation platform capable of creating realistic voices from text.",
            "Voice synthesis technology has advanced significantly in recent years, enabling more natural-sounding speech.",
            "This demo showcases the capabilities of EchoForge for generating human-like speech from text input."
        ],
        "stories": [
            "Once upon a time, in a distant land, there lived a wise old wizard who had mastered the art of voice magic.",
            "The journey to the mountain's peak was arduous, but the view from the top made every step worthwhile.",
            "As the sun set over the horizon, painting the sky in hues of orange and purple, a sense of calm settled over the landscape."
        ]
    }
    
    # Write sample texts to file
    output_path = "static/sample_texts.txt"
    with open(output_path, 'w') as f:
        f.write("# EchoForge Sample Texts\n")
        f.write("# Use these texts to test voice generation\n\n")
        
        for category, texts in sample_texts.items():
            f.write(f"## {category.title()}\n")
            for text in texts:
                f.write(f"{text}\n")
            f.write("\n")
    
    print(f"Created sample texts file: {output_path}")

def check_for_movie_maker_voices():
    """
    Check if movie_maker voice files exist and copy them if they do.
    This helps reuse existing voice files from movie_maker if available.
    """
    # Potential source directories for voice files
    source_dirs = [
        "../movie_maker/hdmy5movie_voices/creative",
        "../movie_maker/voices/creative",
        "../../movie_maker/hdmy5movie_voices/creative",
        "../../movie_maker/voices/creative",
        "/home/tdeshane/movie_maker/hdmy5movie_voices/creative",
        "/home/tdeshane/movie_maker/voices/creative"
    ]
    
    target_dir = "static/voices/creative"
    voice_files_copied = False
    
    # Check each potential source directory
    for source_dir in source_dirs:
        if os.path.exists(source_dir):
            print(f"Found movie_maker voice directory: {source_dir}")
            
            # Get all wav files
            voice_files = [f for f in os.listdir(source_dir) if f.endswith('.wav')]
            
            if voice_files:
                # Create target directory if it doesn't exist
                os.makedirs(target_dir, exist_ok=True)
                
                # Copy voice files
                for voice_file in voice_files:
                    src = os.path.join(source_dir, voice_file)
                    dest = os.path.join(target_dir, voice_file)
                    shutil.copy2(src, dest)
                    print(f"Copied voice file: {src} -> {dest}")
                    voice_files_copied = True
            
            if voice_files_copied:
                print(f"Successfully copied {len(voice_files)} voice files from movie_maker")
                return True
    
    print("No existing movie_maker voice files found")
    return False

def main():
    """Main function to set up voice files for EchoForge."""
    parser = argparse.ArgumentParser(description="Setup voice files for EchoForge")
    parser.add_argument("--force", action="store_true", help="Overwrite existing voice files")
    args = parser.parse_args()
    
    print("\n=== EchoForge Voice Setup ===\n")
    
    # Setup directory structure
    setup_directory_structure()
    
    # Target directory for voice files
    target_dir = "static/voices/creative"
    voice_metadata_path = "static/voices/voice_metadata.txt"
    
    # Check if voice files already exist
    existing_files = [f for f in os.listdir(target_dir) if f.endswith('.wav')] if os.path.exists(target_dir) else []
    
    if existing_files and not args.force:
        print(f"Found {len(existing_files)} existing voice files in {target_dir}")
        print("Using existing voice files. Use --force to regenerate.")
    else:
        # First try to copy from movie_maker if available
        voices_copied = check_for_movie_maker_voices()
        
        # If no voices were copied, generate new ones
        if not voices_copied or args.force:
            print("Generating new voice files...")
            
            # Create voice files for each configuration
            for voice_config in VOICE_CONFIGS:
                speaker_id = voice_config["id"]
                voice_name = voice_config["name"].replace(" ", "_").lower()
                
                # Generate primary voice sample
                primary_filename = os.path.join(target_dir, f"voice_{speaker_id}_{voice_name}.wav")
                create_voice_audio(primary_filename, voice_config)
                
                # Generate alternative versions with slight variations for the same voice
                for variant in range(1, 3):
                    variant_config = voice_config.copy()
                    variant_config["base_freq"] *= (1.0 + (random.random() - 0.5) * 0.05)  # ±2.5% variation
                    variant_config["formant_shift"] *= (1.0 + (random.random() - 0.5) * 0.05)
                    variant_config["duration"] += random.random() - 0.5  # ±0.5s variation
                    
                    variant_filename = os.path.join(
                        target_dir, 
                        f"voice_{speaker_id}_{voice_name}_variant{variant}.wav"
                    )
                    create_voice_audio(variant_filename, variant_config)
    
    # Create metadata file
    create_voice_metadata_file(VOICE_CONFIGS, voice_metadata_path)
    
    # Create sample texts file
    create_default_sample_texts()
    
    print("\n=== Voice Setup Complete ===")
    print(f"Voice files are located in: {os.path.abspath(target_dir)}")
    print("You can now use the EchoForge debug page to test voice generation:")
    print("  1. Start the server: ./start_server.sh")
    print("  2. Navigate to: http://localhost:8765/debug")
    print("  3. Select a speaker ID and enter text to generate")
    print("\nEnjoy creating voices with EchoForge!")

if __name__ == "__main__":
    main() 