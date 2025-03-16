"""
Voice Generator module for EchoForge.

This module provides functionality for generating character voices using the CSM model.
"""

import os
import logging
import time
import uuid
import torch
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union

from app.core import config
from app.models import create_csm_model, CSMModel, PlaceholderCSMModel, CSMModelError

# Setup logging
logger = logging.getLogger(__name__)


class VoiceGenerator:
    """
    Voice Generator for creating character voices.
    
    This class encapsulates the functionality for generating character voices
    using the CSM model with proper fallback mechanisms.
    """
    
    def __init__(
        self,
        model_path: str = config.MODEL_PATH,
        output_dir: str = config.OUTPUT_DIR,
        use_placeholder: bool = False,
    ) -> None:
        """
        Initialize the voice generator.
        
        Args:
            model_path: Path to the model checkpoint
            output_dir: Directory to store generated voice files
            use_placeholder: Whether to use the placeholder model
        """
        self.model_path = model_path
        self.output_dir = output_dir
        self.use_placeholder = use_placeholder
        self.model = None
        self.is_test_mode = os.environ.get("ECHOFORGE_TEST", "false").lower() == "true"
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info("VoiceGenerator initialized with model_path=%s, output_dir=%s", 
                   model_path, output_dir)
    
    def load_model(self) -> bool:
        """
        Load the voice generation model.
        
        Attempts to load the CSM model with proper fallback mechanisms.
        
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
            # Use our CSM model implementation
            logger.info("Loading CSM model from %s", self.model_path)
            
            # Determine the best device to use
            device = self._determine_device()
            
            # Create the CSM model
            self.model = create_csm_model(
                model_path=self.model_path,
                device=device,
                use_placeholder=self.use_placeholder
            )
            
            # Check if we got a placeholder model
            if isinstance(self.model, PlaceholderCSMModel):
                logger.warning("Using placeholder CSM model - real model not available")
            else:
                logger.info("CSM model loaded successfully on device: %s", device)
                
            return True
            
        except Exception as e:
            logger.error("Could not load CSM model: %s", str(e))
            return False
    
    def _determine_device(self) -> str:
        """
        Determine the best device to use for inference.
        
        Returns:
            str: 'cuda' if available with enough memory, otherwise 'cpu'
        """
        # Check if CUDA is available
        if torch.cuda.is_available():
            try:
                # Check if there's enough GPU memory (at least 2GB free)
                free_memory = torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)
                free_memory_gb = free_memory / (1024 ** 3)
                
                if free_memory_gb >= 2.0:
                    logger.info(f"Using CUDA device with {free_memory_gb:.2f} GB free memory")
                    return "cuda"
                else:
                    logger.warning(f"Not enough GPU memory ({free_memory_gb:.2f} GB free), falling back to CPU")
                    return "cpu"
            except Exception as e:
                logger.warning(f"Error checking GPU memory: {e}, falling back to CPU")
                return "cpu"
        
        logger.info("CUDA not available, using CPU")
        return "cpu"
    
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
            speaker_id: Speaker ID to use
            temperature: Temperature for sampling (higher = more diverse)
            top_k: Number of highest probability tokens to consider
            style: Voice style to use (not used in current CSM implementation)
            device: Device to use for inference (auto, cuda, or cpu)
            
        Returns:
            Tuple containing:
                - Path to the generated audio file (or None if failed)
                - URL to access the file (or None if failed)
        """
        # Ensure model is loaded
        if self.model is None:
            if not self.load_model():
                logger.error("Failed to load model")
                return None, None
        
        # Generate a unique filename
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        filename = f"voice_{timestamp}_{unique_id}.wav"
        output_path = os.path.join(self.output_dir, filename)
        
        try:
            logger.info(f"Generating voice for text: '{text}' with speaker_id={speaker_id}, "
                       f"temperature={temperature}, top_k={top_k}")
            
            # Generate speech
            audio, sample_rate = self.model.generate_speech(
                text=text,
                speaker_id=speaker_id,
                temperature=temperature,
                top_k=top_k,
            )
            
            # Save the audio
            self.model.save_audio(audio, sample_rate, output_path)
            
            # Check if file was created
            if not os.path.exists(output_path):
                logger.error(f"Output file not created: {output_path}")
                return None, None
            
            # Create URL for accessing the file
            # Use relative path from output_dir to create URL
            relative_path = os.path.relpath(output_path, self.output_dir)
            url = f"/voices/{relative_path}"
            
            logger.info(f"Voice generated successfully: {output_path}")
            return output_path, url
            
        except CSMModelError as e:
            logger.error(f"CSM model error: {e}")
            return None, None
        except Exception as e:
            logger.error(f"Error generating voice: {e}")
            return None, None
    
    def list_available_voices(self) -> List[Dict[str, Any]]:
        """
        List available voice files.
        
        Returns:
            List of dictionaries containing voice file information
        """
        voices = []
        try:
            # Get all WAV files in the output directory
            output_dir = Path(self.output_dir)
            if not output_dir.exists():
                logger.warning(f"Output directory does not exist: {output_dir}")
                return voices
            
            # Find all WAV files
            wav_files = list(output_dir.glob("**/*.wav"))
            
            for wav_path in wav_files:
                # Get file stats
                stats = wav_path.stat()
                
                # Create relative URL
                relative_path = wav_path.relative_to(output_dir)
                url = f"/voices/{relative_path}"
                
                # Extract metadata from filename
                filename = wav_path.name
                parts = filename.split('_')
                
                # Try to extract timestamp and ID
                timestamp = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                voice_id = parts[2].split('.')[0] if len(parts) > 2 else "unknown"
                
                # Add voice info
                voices.append({
                    "id": voice_id,
                    "filename": filename,
                    "path": str(wav_path),
                    "url": url,
                    "size_bytes": stats.st_size,
                    "created_at": stats.st_ctime,
                    "modified_at": stats.st_mtime,
                })
            
            # Sort by creation time (newest first)
            voices.sort(key=lambda v: v["created_at"], reverse=True)
            
            return voices
            
        except Exception as e:
            logger.error(f"Error listing voices: {e}")
            return []
    
    def cleanup_old_files(self, max_age_hours: int = config.VOICE_FILE_MAX_AGE_HOURS) -> int:
        """
        Clean up old voice files.
        
        Args:
            max_age_hours: Maximum age of files to keep (in hours)
            
        Returns:
            Number of files deleted
        """
        try:
            # Get current time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            # Get all WAV files in the output directory
            output_dir = Path(self.output_dir)
            if not output_dir.exists():
                logger.warning(f"Output directory does not exist: {output_dir}")
                return 0
            
            # Find all WAV files
            wav_files = list(output_dir.glob("**/*.wav"))
            
            # Count deleted files
            deleted_count = 0
            
            for wav_path in wav_files:
                # Get file stats
                stats = wav_path.stat()
                
                # Check if file is older than max age
                if current_time - stats.st_mtime > max_age_seconds:
                    # Delete file
                    wav_path.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old voice file: {wav_path}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old voice files")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")
            return 0


class MockModel:
    """Mock model for testing."""
    
    def __init__(self):
        """Initialize the mock model."""
        self.sample_rate = 24000
    
    def generate_speech(self, text: str, speaker_id: int = 1, temperature: float = 0.5, top_k: int = 50) -> Tuple[torch.Tensor, int]:
        """
        Generate a mock speech tensor.
        
        Args:
            text: Text to convert to speech
            speaker_id: Speaker ID to use
            temperature: Temperature for sampling
            top_k: Number of highest probability tokens to consider
            
        Returns:
            Tuple containing:
                - Mock audio tensor
                - Sample rate
        """
        # Generate a simple sine wave
        duration_sec = min(len(text) * 0.1, 10)  # Roughly 0.1 seconds per character, max 10 seconds
        t = torch.arange(0, duration_sec, 1/self.sample_rate)
        
        # Generate different frequencies based on speaker_id
        frequency = 220 + (speaker_id * 55)  # A3 + speaker_id * semitones
        
        # Create a simple sine wave
        audio = torch.sin(2 * torch.pi * frequency * t)
        
        # Add some variation based on temperature and top_k
        amplitude_mod = temperature * 0.1 * torch.sin(2 * torch.pi * (top_k / 10) * t)
        audio = audio + amplitude_mod
        
        # Normalize
        audio = audio / audio.abs().max()
        
        return audio, self.sample_rate
    
    def save_audio(self, audio: torch.Tensor, sample_rate: int, output_path: str) -> str:
        """
        Save mock audio to a file.
        
        Args:
            audio: Audio tensor
            sample_rate: Sample rate
            output_path: Path to save the audio
            
        Returns:
            Path to the saved audio file
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save audio using torchaudio
        import torchaudio
        torchaudio.save(output_path, audio.unsqueeze(0), sample_rate)
        
        return output_path


# Create a singleton instance for application-wide use
voice_generator = VoiceGenerator() 