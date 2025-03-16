"""
Voice Generator module for EchoForge.

This module provides functionality for generating character voices using the CSM model.
"""

import os
import logging
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union

from app.core import config

# Setup logging
logger = logging.getLogger(__name__)


class VoiceGenerator:
    """
    Voice Generator for creating character voices.
    
    This class encapsulates the functionality for generating character voices
    using either the CSM model or the VoiceCloner as a fallback.
    """
    
    def __init__(
        self,
        model_path: str = config.MODEL_PATH,
        output_dir: str = config.OUTPUT_DIR,
    ) -> None:
        """
        Initialize the voice generator.
        
        Args:
            model_path: Path to the model checkpoint
            output_dir: Directory to store generated voice files
        """
        self.model_path = model_path
        self.output_dir = output_dir
        self.model = None
        self.is_test_mode = os.environ.get("ECHOFORGE_TEST", "false").lower() == "true"
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info("VoiceGenerator initialized with model_path=%s, output_dir=%s", 
                   model_path, output_dir)
    
    def load_model(self) -> bool:
        """
        Load the voice generation model.
        
        Attempts to load the CSM model first, and falls back to VoiceCloner if necessary.
        
        Returns:
            bool: True if model was loaded successfully, False otherwise
        """
        if self.model is not None:
            logger.info("Model already loaded")
            return True
            
        # In test mode, use a mock model
        if self.is_test_mode:
            logger.info("Using mock model for testing")
            self.model = MockModel()
            return True
        
        try:
            # Try to import CSM model
            try:
                from csm.models import CSMModel
                logger.info("Importing CSM model from %s", self.model_path)
                self.model = CSMModel.from_pretrained(self.model_path)
                logger.info("Model loaded successfully")
                return True
            except ImportError:
                # Fall back to VoiceCloner if CSM model is not available
                logger.warning("CSM model not available, falling back to VoiceCloner")
                from voice_poc.utils.voice_cloner import VoiceCloner
                self.model = VoiceCloner()
                logger.info("Loaded model using VoiceCloner")
                return True
        except Exception as e:
            logger.error("Could not import CSM model or VoiceCloner: %s", str(e))
            return False
    
    def generate(
        self,
        text: str,
        speaker_id: int = config.DEFAULT_SPEAKER_ID,
        temperature: float = config.DEFAULT_TEMPERATURE,
        top_k: int = config.DEFAULT_TOP_K,
        style: str = config.DEFAULT_STYLE,
        device: str = config.DEFAULT_DEVICE,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate voice from text.
        
        Args:
            text: Text to convert to speech
            speaker_id: ID of the speaker voice to use
            temperature: Temperature for generation (0.0-1.0)
            top_k: Top-k for generation
            style: Voice style (short, medium, long)
            device: Device to run generation on (cpu, cuda)
            
        Returns:
            Tuple of (output_path, error_message)
            - output_path: Path to the generated voice file, or None if generation failed
            - error_message: Error message if generation failed, or None if generation succeeded
        """
        # Validate text
        if not text.strip():
            return None, "Text cannot be empty"
        
        # Load model if not already loaded
        if self.model is None and not self.load_model():
            return None, "Failed to load voice model"
        
        # Generate unique filename
        file_id = uuid.uuid4().hex[:8]
        output_filename = f"voice_{speaker_id}_{file_id}.wav"
        output_path = os.path.join(self.output_dir, output_filename)
        
        try:
            logger.info("Generating voice for text: '%s'", text[:50] + "..." if len(text) > 50 else text)
            
            # Call the appropriate generation method
            if hasattr(self.model, "generate_speech"):
                # CSM model
                self.model.generate_speech(
                    text=text,
                    speaker_id=speaker_id,
                    temperature=temperature,
                    top_k=top_k,
                    style=style,
                    device=device,
                    output_path=output_path
                )
            elif hasattr(self.model, "generate_direct"):
                # VoiceCloner
                self.model.generate_direct(
                    text=text,
                    speaker_id=speaker_id,
                    temperature=temperature,
                    top_k=top_k,
                    style=style,
                    output_file=output_path
                )
            elif hasattr(self.model, "mock_generate"):
                # Mock model for testing
                self.model.mock_generate(output_path)
            else:
                return None, "Model doesn't have a suitable generation method"
            
            # Check if file was created
            if not os.path.exists(output_path):
                return None, "Voice file was not created"
            
            logger.info("Voice generated successfully: %s", output_path)
            return output_path, None
            
        except Exception as e:
            logger.error("Error generating voice: %s", str(e), exc_info=True)
            return None, f"Error generating voice: {str(e)}"
    
    def list_available_voices(self) -> List[Dict[str, Any]]:
        """
        List available voices with metadata.
        
        Returns:
            List of voice information dictionaries
        """
        # In a real implementation, this would query available voices from a database
        # or model. For now, we'll return a static list of example voices.
        return [
            {
                "speaker_id": 1,
                "name": "Male Commander",
                "gender": "male",
                "description": "Authoritative male voice with clear diction and commanding presence.",
                "sample_url": "/static/samples/male_commander.wav"
            },
            {
                "speaker_id": 2,
                "name": "Female Scientist",
                "gender": "female",
                "description": "Professional female voice with precise articulation and thoughtful cadence.",
                "sample_url": "/static/samples/female_scientist.wav"
            },
            {
                "speaker_id": 3,
                "name": "Young Hero",
                "gender": "male",
                "description": "Energetic young male voice with enthusiasm and determination.",
                "sample_url": "/static/samples/young_hero.wav"
            },
            {
                "speaker_id": 4,
                "name": "Wise Elder",
                "gender": "female",
                "description": "Gentle elderly female voice with wisdom and warmth.",
                "sample_url": "/static/samples/wise_elder.wav"
            }
        ]
    
    def cleanup_old_files(self, max_age_hours: int = config.VOICE_FILE_MAX_AGE_HOURS) -> int:
        """
        Clean up old voice files.
        
        Args:
            max_age_hours: Maximum age of files to keep in hours
            
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        try:
            voice_dir = Path(self.output_dir)
            for file_path in voice_dir.glob("voice_*.wav"):
                # Check file age
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info("Cleaned up %d old voice files", deleted_count)
            
            return deleted_count
        except Exception as e:
            logger.error("Error cleaning up old files: %s", str(e))
            return 0


class MockModel:
    """Mock model implementation for testing without actual ML models."""
    
    def __init__(self):
        """Initialize the mock model."""
        logger.info("Mock model initialized")
    
    def mock_generate(self, output_path: str) -> None:
        """
        Create a mock audio file for testing.
        
        Args:
            output_path: Path to save the mock audio file
        """
        logger.info(f"Mock generating audio to {output_path}")
        # Create a tiny WAV file
        with open(output_path, 'wb') as f:
            # WAV header for a minimal silent file
            f.write(b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00')
        
        # Simulate generation delay
        time.sleep(0.5)


# Create a singleton instance for application-wide use
voice_generator = VoiceGenerator() 