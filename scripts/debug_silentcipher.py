#!/usr/bin/env python3
"""
Debug script to test silentcipher directly.
This helps understand how to properly use the silentcipher package.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("debug_silentcipher")

def test_silentcipher():
    """Test silentcipher directly."""
    try:
        import silentcipher
        logger.info(f"Successfully imported silentcipher {getattr(silentcipher, '__version__', 'unknown')}")
        
        # Print available modules and classes
        logger.info(f"Available modules in silentcipher: {dir(silentcipher)}")
        
        # Try to use the TextToSpeechModel
        try:
            logger.info("Trying to import TextToSpeechModel")
            from silentcipher.models import TextToSpeechModel
            logger.info("Successfully imported TextToSpeechModel")
            
            # Try to create the model
            logger.info("Creating TextToSpeechModel instance")
            
            # First try with CPU explicitly
            model = TextToSpeechModel(device="cpu")
            logger.info("Successfully created TextToSpeechModel with CPU")
            
            # Generate speech
            logger.info("Generating speech")
            text = "This is a test of the silentcipher text to speech system."
            audio = model.generate_speech(text=text, speaker_id=1, temperature=0.9, top_k=50)
            logger.info(f"Generated audio of shape {audio.shape}")
            
            # Save the audio
            import torch
            import torchaudio
            output_path = "test_silentcipher.wav"
            torchaudio.save(output_path, audio.unsqueeze(0), 24000)
            logger.info(f"Saved audio to {output_path}")
            
            logger.info("Silentcipher test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error with TextToSpeechModel: {e}")
            
            # Try alternative approach if available
            logger.info("Trying alternative approach")
            if hasattr(silentcipher, "generate_speech"):
                audio = silentcipher.generate_speech(
                    text="This is a test using the direct generate_speech function.",
                    speaker_id=1,
                    temperature=0.9
                )
                logger.info(f"Generated audio using direct function")
                return True
    
    except ImportError as e:
        logger.error(f"Error importing silentcipher: {e}")
        return False
    
    return False

if __name__ == "__main__":
    success = test_silentcipher()
    if success:
        logger.info("Test completed successfully")
        sys.exit(0)
    else:
        logger.error("Test failed")
        sys.exit(1) 