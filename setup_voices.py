#!/usr/bin/env python3
"""
Setup Voice Files for EchoForge

This script generates high-quality voice samples for the EchoForge application
using the CSM voice generation model. It creates a set of voice files with 
different characteristics and places them in the correct locations.

Usage:
    python setup_voices.py [--force] [--cpu]

Options:
    --force    Overwrite existing voice files if they exist
    --cpu      Force CPU usage instead of GPU (slower but works on all systems)

Requirements for high-quality voice generation:
    1. csm-voice-cloning directory must be set up:
       - This directory should contain: generator.py, models.py, etc.
    
    2. Required Python packages (install with pip):
       - torch==2.4.0
       - torchaudio==2.4.0
       - transformers==4.49.0
       - huggingface_hub==0.28.1
       - moshi==0.2.2
       - torchtune==0.4.0
       - torchao==0.9.0
       - silentcipher (from GitHub)
       
    You can install all required packages with:
    pip install -r csm-voice-cloning/requirements.txt

The script will:
1. Create the necessary directory structure
2. Download the CSM voice generation model
3. Generate realistic voice samples with different characteristics
4. Place them in the correct locations for EchoForge to use
"""

import os
import sys
import argparse
import json
import time
import random
from pathlib import Path

# Handle the CSM model import
try:
    # Try to import from csm-voice-cloning directory
    sys.path.append(os.path.join(os.path.dirname(__file__), 'csm-voice-cloning'))
    from generator import load_csm_1b, Segment
    CSM_AVAILABLE = True
    print("Successfully imported CSM modules from csm-voice-cloning")
except ImportError as e:
    print(f"Warning: CSM voice generation modules not found: {e}")
    print("Voice files will be generated using basic waveforms instead")
    print("For high-quality voices, ensure the csm-voice-cloning directory is present")
    print("and all dependencies are installed (see requirements.txt in that directory)")
    CSM_AVAILABLE = False

# Try to import torch, required for CSM
try:
    import torch
    import torchaudio
    from huggingface_hub import hf_hub_download
    TORCH_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PyTorch not found: {e}")
    print("Install required packages with: pip install -r csm-voice-cloning/requirements.txt")
    TORCH_AVAILABLE = False
    
# Try to import other required packages for CSM
if CSM_AVAILABLE and TORCH_AVAILABLE:
    try:
        # These imports are just to check if the packages are available
        import moshi
        import transformers
        import tokenizers
        ALL_DEPS_AVAILABLE = True
    except ImportError as e:
        print(f"Warning: Additional dependencies for CSM not found: {e}")
        print("Install required packages with: pip install -r csm-voice-cloning/requirements.txt")
        ALL_DEPS_AVAILABLE = False
else:
    ALL_DEPS_AVAILABLE = False
    
# Only if dependencies are unavailable, import numpy for basic waveform generation
if not ALL_DEPS_AVAILABLE:
    import numpy as np
    import wave
    import struct

# Voice configurations with detailed parameters for CSM model
VOICE_CONFIGS = [
    {
        "id": 1,
        "name": "Commander Sterling",
        "gender": "male",
        "description": "Deep authoritative voice with confident tone",
        "speaker_id": 4,  # Maps to CSM speaker with gravitas
        "temperature": 0.8,  # Lower temperature for more consistent output
        "topk": 40,
        "character_traits": "confident, commanding, authoritative",
        "sample_text": "The mission briefing is clear. We must secure the perimeter and establish a base of operations immediately."
    },
    {
        "id": 2,
        "name": "Dr. Elise Jensen",
        "gender": "female",
        "description": "Clear, articulate voice with professional tone",
        "speaker_id": 2,  # Maps to CSM medium-pitched female
        "temperature": 0.9,
        "topk": 45,
        "character_traits": "intelligent, precise, professional",
        "sample_text": "The analysis confirms our hypothesis. The compound exhibits remarkable properties under these specific conditions."
    },
    {
        "id": 3,
        "name": "James Fletcher",
        "gender": "male",
        "description": "Warm, friendly voice with natural cadence",
        "speaker_id": 0,  # Maps to CSM clear articulation male
        "temperature": 1.0,
        "topk": 50,
        "character_traits": "warm, friendly, approachable",
        "sample_text": "It's great to see everyone here today. I'm looking forward to getting to know each of you better as we work together."
    },
    {
        "id": 4,
        "name": "Sophia Chen",
        "gender": "female",
        "description": "Energetic voice with varied intonation",
        "speaker_id": 5,  # Maps to CSM smooth female with warm tone
        "temperature": 1.1,  # Higher temperature for more variation
        "topk": 50,
        "character_traits": "energetic, expressive, dynamic",
        "sample_text": "The innovation challenge starts now! Every idea counts, so don't hold back. Let's transform the way people think about this!"
    },
    {
        "id": 5,
        "name": "Morgan Riley",
        "gender": "neutral",
        "description": "Balanced, neutral voice with moderate tone",
        "speaker_id": 3,  # Maps to CSM higher pitched voice
        "temperature": 0.9,
        "topk": 45,
        "character_traits": "balanced, neutral, versatile",
        "sample_text": "Consider all perspectives before making your decision. Each option has its own merits and challenges to navigate."
    }
]

# Alternative texts for generating additional voice samples for the same speaker
ALTERNATIVE_TEXTS = [
    "Welcome to EchoForge, the advanced voice generation system that creates realistic speech.",
    "The purpose of this demonstration is to showcase the capabilities of our voice synthesis technology.",
    "This sample demonstrates the tonal qualities and speech patterns characteristic of this voice type.",
    "Voice generation has many applications in creative media, accessibility, and user interfaces.",
    "When properly implemented, synthetic voices can sound remarkably natural and expressive."
]

def create_basic_voice_audio(filename, voice_config, sample_rate=22050):
    """
    Create a basic voice audio file using sine waves when CSM is not available.
    This is a fallback method that creates distinctive but simple voice patterns.
    """
    # Extract parameters from voice config
    voice_id = voice_config["id"]
    gender = voice_config["gender"]
    
    # Set base frequency based on gender
    if gender == "male":
        base_freq = 120.0
    elif gender == "female":
        base_freq = 220.0
    else:  # neutral
        base_freq = 165.0
    
    # Adjust slightly based on voice ID for variety
    base_freq *= (1.0 + (voice_id - 3) * 0.05)
    
    # Parameters
    duration = 4.0  # seconds
    amplitude = 24000  # Volume (16-bit max is 32767)
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
        formant_freq = base_freq * harmonic * (0.9 if gender == "male" else 1.1 if gender == "female" else 1.0)
        audio_data += harmonic_amp * np.sin(2 * np.pi * formant_freq * t)
    
    # Add some noise for breathiness
    noise = np.random.normal(0, amplitude * 0.05, num_samples)
    audio_data += noise
    
    # Apply envelope
    envelope = np.ones(num_samples)
    attack = int(0.1 * sample_rate)
    release = int(0.2 * sample_rate)
    
    # Attack phase
    envelope[:attack] = np.linspace(0, 1, attack)
    # Release phase
    envelope[-release:] = np.linspace(1, 0, release)
    
    audio_data = audio_data * envelope
    
    # Ensure we stay within 16-bit range
    audio_data = np.clip(audio_data, -32767, 32767).astype(np.int16)
    
    # Create WAV file
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16 bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    print(f"Created basic voice file: {filename}")
    return filename

def generate_csm_voice(generator, voice_config, output_filename):
    """
    Generate a high-quality voice sample using the CSM model.
    
    Args:
        generator: CSM voice generator
        voice_config: Dictionary with voice parameters
        output_filename: Where to save the generated audio
    """
    # Extract parameters
    speaker_id = voice_config["speaker_id"]
    temperature = voice_config["temperature"]
    topk = voice_config["topk"]
    text = voice_config["sample_text"]
    
    print(f"Generating voice sample: {voice_config['name']} (speaker={speaker_id}, temp={temperature})")
    
    # Generate audio with CSM
    try:
        audio = generator.generate(
            text=text,
            speaker=speaker_id,
            context=[],
            max_audio_length_ms=15000,
            temperature=temperature,
            topk=topk
        )
        
        # Save the audio
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        torchaudio.save(output_filename, audio.unsqueeze(0).cpu(), generator.sample_rate)
        print(f"Created CSM voice file: {output_filename}")
        return True
    except Exception as e:
        print(f"Error generating CSM voice: {e}")
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
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write("# EchoForge Voice Metadata\n")
        f.write("# This file contains information about available voices\n\n")
        
        for voice in voice_configs:
            f.write(f"## Voice ID: {voice['id']}\n")
            f.write(f"Name: {voice['name']}\n")
            f.write(f"Gender: {voice['gender']}\n")
            f.write(f"Description: {voice['description']}\n")
            f.write(f"Character Traits: {voice['character_traits']}\n")
            f.write(f"Sample Text: \"{voice['sample_text']}\"\n\n")
    
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
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write("# EchoForge Sample Texts\n")
        f.write("# Use these texts to test voice generation\n\n")
        
        for category, texts in sample_texts.items():
            f.write(f"## {category.title()}\n")
            for text in texts:
                f.write(f"{text}\n")
            f.write("\n")
    
    print(f"Created sample texts file: {output_path}")

def main():
    """Main function to set up voice files for EchoForge."""
    parser = argparse.ArgumentParser(description="Setup voice files for EchoForge")
    parser.add_argument("--force", action="store_true", help="Overwrite existing voice files")
    parser.add_argument("--cpu", action="store_true", help="Force CPU usage (slower but works on all systems)")
    parser.add_argument("--skip-deps-check", action="store_true", help="Skip dependency checks and try to run anyway")
    args = parser.parse_args()
    
    print("\n=== EchoForge Voice Setup ===\n")
    
    # Print dependency status
    if not args.skip_deps_check:
        print("Dependency Status:")
        print(f"  PyTorch Available: {'Yes' if TORCH_AVAILABLE else 'No'}")
        print(f"  CSM Modules Available: {'Yes' if CSM_AVAILABLE else 'No'}")
        print(f"  All Dependencies Available: {'Yes' if ALL_DEPS_AVAILABLE else 'No'}")
        print("")
    
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
        # Check if we have all the required dependencies for CSM
        if ALL_DEPS_AVAILABLE or args.skip_deps_check:
            # Determine device for CSM model
            device = "cpu" if args.cpu else "cuda" if torch.cuda.is_available() else "cpu"
            if device == "cpu" and not args.cpu:
                print("CUDA not available, falling back to CPU (use --cpu to avoid this message)")
            
            # Generate voice files using CSM
            try:
                # Download CSM model
                print("Downloading CSM voice model...")
                model_path = hf_hub_download(repo_id="sesame/csm-1b", filename="ckpt.pt")
                print(f"Model downloaded to: {model_path}")
                
                # Load CSM generator
                print(f"Loading CSM model on {device}...")
                generator = load_csm_1b(model_path, device)
                print("CSM model loaded successfully")
                
                # Generate voice files
                print("\nGenerating high-quality voice files with CSM model...")
                for voice_config in VOICE_CONFIGS:
                    voice_id = voice_config["id"]
                    voice_name = voice_config["name"].replace(" ", "_").lower()
                    
                    # Generate primary voice sample
                    primary_filename = os.path.join(target_dir, f"voice_{voice_id}_{voice_name}.wav")
                    success = generate_csm_voice(generator, voice_config, primary_filename)
                    
                    if success:
                        # Generate alternative versions with the same voice but different text
                        for i, alt_text in enumerate(ALTERNATIVE_TEXTS[:2]):  # Just use 2 alternatives to save time
                            variant_config = voice_config.copy()
                            variant_config["sample_text"] = alt_text
                            
                            # Slightly vary the parameters
                            variant_config["temperature"] = voice_config["temperature"] * (1.0 + (random.random() - 0.5) * 0.1)
                            
                            variant_filename = os.path.join(
                                target_dir, 
                                f"voice_{voice_id}_{voice_name}_variant{i+1}.wav"
                            )
                            generate_csm_voice(generator, variant_config, variant_filename)
                
                print("Finished generating voices with CSM model")
                
            except Exception as e:
                print(f"Error with CSM voice generation: {e}")
                print("Falling back to basic voice generation...")
                generate_basic_voices(target_dir)
        else:
            print("\nUsing basic voice generation since CSM model dependencies are not available")
            print("To use high-quality voice generation, install the required dependencies:")
            print("pip install -r csm-voice-cloning/requirements.txt")
            generate_basic_voices(target_dir)
    
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

def generate_basic_voices(target_dir):
    """Generate basic voice files when CSM is not available."""
    print("\nGenerating basic voice files...")
    
    for voice_config in VOICE_CONFIGS:
        voice_id = voice_config["id"]
        voice_name = voice_config["name"].replace(" ", "_").lower()
        
        # Generate primary voice sample
        primary_filename = os.path.join(target_dir, f"voice_{voice_id}_{voice_name}.wav")
        create_basic_voice_audio(primary_filename, voice_config)
        
        # Generate a couple of variants
        for variant in range(1, 3):
            # Make a copy of the config with slight variations
            variant_config = voice_config.copy()
            
            # Just modify the ID slightly to get different waveforms
            variant_config["id"] = voice_config["id"] + variant * 0.1
            
            variant_filename = os.path.join(
                target_dir, 
                f"voice_{voice_id}_{voice_name}_variant{variant}.wav"
            )
            create_basic_voice_audio(variant_filename, variant_config)
    
    print("Basic voice generation complete")

if __name__ == "__main__":
    # Set a seed for reproducibility
    random.seed(42)
    if TORCH_AVAILABLE:
        torch.manual_seed(42)
    main() 