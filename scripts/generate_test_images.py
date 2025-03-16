#!/usr/bin/env python
"""
Generate test images for EchoForge character showcase.

This script creates simple colored images with text labels for testing
the character showcase UI. It generates images for male, female, and
neutral characters with different colors.
"""

import os
from PIL import Image, ImageDraw, ImageFont
import random

# Configuration
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'images')
SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'samples')
IMAGE_SIZE = (400, 400)
GENDERS = ['male', 'female', 'neutral']
COLORS = {
    'male': [(50, 100, 200), (70, 120, 220), (90, 140, 240)],
    'female': [(200, 100, 150), (220, 120, 170), (240, 140, 190)],
    'neutral': [(100, 180, 100), (120, 200, 120), (140, 220, 140)]
}

def create_directories():
    """Create output directories if they don't exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(SAMPLE_DIR, exist_ok=True)
    print(f"Created directories: {OUTPUT_DIR} and {SAMPLE_DIR}")

def generate_character_image(gender, number):
    """Generate a simple colored image with text for a character."""
    # Select a random color from the gender's color palette
    color = random.choice(COLORS[gender])
    
    # Create a new image with the selected color
    img = Image.new('RGB', IMAGE_SIZE, color)
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        font = ImageFont.load_default()
    
    # Add text to the image
    text = f"{gender.capitalize()} {number}"
    text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else (200, 40)
    position = ((IMAGE_SIZE[0] - text_width) // 2, (IMAGE_SIZE[1] - text_height) // 2)
    
    # Draw text with a shadow for better visibility
    shadow_position = (position[0] + 2, position[1] + 2)
    draw.text(shadow_position, text, fill=(0, 0, 0), font=font)
    draw.text(position, text, fill=(255, 255, 255), font=font)
    
    # Save the image
    filename = f"{gender}{number}.jpg"
    filepath = os.path.join(OUTPUT_DIR, filename)
    img.save(filepath, "JPEG", quality=90)
    print(f"Generated image: {filepath}")
    
    return filename

def create_empty_audio_file(filename):
    """Create an empty audio file for testing."""
    filepath = os.path.join(SAMPLE_DIR, filename)
    
    # Create an empty file
    with open(filepath, 'wb') as f:
        # Write a minimal WAV header
        f.write(b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00')
    
    print(f"Created empty audio file: {filepath}")

def main():
    """Generate test images and audio files for all genders and numbers."""
    create_directories()
    
    # Generate 5 images for each gender
    for gender in GENDERS:
        for i in range(1, 6):
            filename = generate_character_image(gender, i)
            audio_filename = f"voice_{gender[0]}{i}_sample.mp3"
            create_empty_audio_file(audio_filename)
    
    print("Done! Generated 15 test images and audio files.")

if __name__ == "__main__":
    main() 