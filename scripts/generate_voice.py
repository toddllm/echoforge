#!/usr/bin/env python3
"""
Simple Voice Generation Script

This script demonstrates how to use the CSM model to generate speech on CPU.
It can be used as a standalone tool for quick voice generation.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the project root to the Python path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("generate_voice")

def main():
    """Main function for voice generation script."""
    parser = argparse.ArgumentParser(description="Generate voice using CSM model")
    parser.add_argument("--text", required=True, help="Text to convert to speech")
    parser.add_argument("--output", default=None, help="Output file path (default: auto-generated)")
    parser.add_argument("--device", choices=["cpu", "cuda", "auto"], default="cpu", 
                        help="Device to use for generation (default: cpu)")
    parser.add_argument("--speaker-id", type=int, default=1, help="Speaker ID to use (default: 1)")
    parser.add_argument("--temperature", type=float, default=0.7, 
                        help="Temperature for sampling (default: 0.7)")
    parser.add_argument("--top-k", type=int, default=50, 
                        help="Top-k tokens to consider (default: 50)")
    parser.add_argument("--model-path", default=None, 
                        help="Path to model checkpoint (default: auto-download)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Import here to avoid loading modules unnecessarily
    try:
        from app.models import create_csm_model
    except ImportError as e:
        logger.error(f"Error importing modules: {e}")
        logger.error("Make sure you're running this script from the project root or have added it to PYTHONPATH")
        sys.exit(1)
    
    # Create output directory if needed
    if args.output:
        output_path = Path(args.output)
        os.makedirs(output_path.parent, exist_ok=True)
    else:
        # Auto-generate output path
        output_dir = project_root / "generated"
        os.makedirs(output_dir, exist_ok=True)
        output_path = output_dir / f"voice_{args.speaker_id}_{int(args.temperature*10)}_{args.top_k}.wav"
    
    logger.info(f"Will save output to: {output_path}")
    
    # Create and initialize the model
    try:
        logger.info(f"Creating CSM model with device={args.device}")
        model = create_csm_model(model_path=args.model_path, device=args.device)
        
        # Generate speech
        logger.info(f"Generating speech for text: '{args.text}'")
        audio, sample_rate = model.generate_speech(
            text=args.text,
            speaker_id=args.speaker_id,
            temperature=args.temperature,
            top_k=args.top_k
        )
        
        # Save audio
        logger.info(f"Saving audio to {output_path}")
        model.save_audio(audio, sample_rate, str(output_path))
        
        logger.info(f"Successfully generated speech at: {output_path}")
        print(f"Generated speech saved to: {output_path}")
        
    except Exception as e:
        logger.exception(f"Error during speech generation: {e}")
        sys.exit(1)
    finally:
        # Clean up
        if 'model' in locals():
            model.cleanup()

if __name__ == "__main__":
    main() 