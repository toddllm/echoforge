#!/usr/bin/env python3
"""
CSM Model Example

This script demonstrates how to use the CSM model for text-to-speech generation.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the CSM model
from app.models import create_csm_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("csm_example")


def main():
    """Run the CSM model example."""
    parser = argparse.ArgumentParser(description="CSM Model Example")
    parser.add_argument("--text", type=str, default="Hello, world! This is a test of the CSM model.",
                        help="Text to convert to speech")
    parser.add_argument("--speaker-id", type=int, default=1,
                        help="Speaker ID to use")
    parser.add_argument("--temperature", type=float, default=0.9,
                        help="Temperature for sampling")
    parser.add_argument("--top-k", type=int, default=50,
                        help="Top-k for sampling")
    parser.add_argument("--device", type=str, default=None,
                        help="Device to use (cuda or cpu)")
    parser.add_argument("--output", type=str, default="output.wav",
                        help="Output file path")
    parser.add_argument("--use-placeholder", action="store_true",
                        help="Use placeholder model instead of real model")
    args = parser.parse_args()

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        # Create the CSM model
        logger.info("Creating CSM model...")
        model = create_csm_model(device=args.device, use_placeholder=args.use_placeholder)

        # Generate speech
        logger.info(f"Generating speech for text: '{args.text}'")
        audio, sample_rate = model.generate_speech(
            text=args.text,
            speaker_id=args.speaker_id,
            temperature=args.temperature,
            top_k=args.top_k
        )

        # Save the audio
        logger.info(f"Saving audio to {args.output}")
        model.save_audio(audio, sample_rate, args.output)

        # Clean up
        model.cleanup()

        logger.info("Done!")
        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 