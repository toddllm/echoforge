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
import sys

from app.core import config
from app.models import (
    create_csm_model, CSMModel, PlaceholderCSMModel, CSMModelError,
    create_direct_csm, DirectCSM, DirectCSMError
)

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
        use_direct_csm: bool = config.USE_DIRECT_CSM,  # Use config setting
    ) -> None:
        """
        Initialize the voice generator.
        
        Args:
            model_path: Path to the model checkpoint
            output_dir: Directory to store generated voice files
            use_placeholder: Whether to use the placeholder model
            use_direct_csm: Whether to use the direct CSM implementation
        """
        self.model_path = model_path
        self.output_dir = output_dir
        self.use_placeholder = use_placeholder
        self.use_direct_csm = use_direct_csm
        self.model = None
        self.direct_csm = None
        self.is_test_mode = os.environ.get("ECHOFORGE_TEST", "false").lower() == "true"
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info("VoiceGenerator initialized with model_path=%s, output_dir=%s, use_direct_csm=%s", 
                   model_path, output_dir, use_direct_csm)
    
    def initialize(self, device: str = None) -> bool:
        """
        Initialize the voice generator by loading the model.
        
        This is an alias for load_model for compatibility.
        
        Args:
            device: Device to use for inference ('auto', 'cuda', or 'cpu')
            
        Returns:
            bool: True if model was loaded successfully, False otherwise
        """
        return self.load_model(device)
    
    def is_initialized(self) -> bool:
        """
        Check if the model is initialized.
        
        Returns:
            bool: True if model is loaded, False otherwise
        """
        return self.model is not None or self.direct_csm is not None
    
    def load_model(self, device: str = None) -> bool:
        """
        Load the voice generation model.
        
        Attempts to load the CSM model. Will try CUDA if available, then fall back to CPU if needed.
        Will not use a placeholder model.
        
        Args:
            device: Device to use for inference ('auto', 'cuda', or 'cpu')
        
        Returns:
            bool: True if model was loaded successfully, False otherwise
        """
        if self.model is not None or self.direct_csm is not None:
            logger.info("Model already loaded")
            return True
            
        # In test mode, use a mock model
        if self.is_test_mode:
            logger.info("Using mock model for testing")
            self.model = MockModel()
            return True
        
        try:
            # Determine the best device to use
            if device is None or device == "auto":
                device = self._determine_device()
            else:
                # Validate the device
                if device == "cuda" and not torch.cuda.is_available():
                    logger.warning("CUDA requested but not available, falling back to CPU")
                    device = "cpu"
                logger.info(f"Using explicitly requested device: {device}")
            
            # Try to load the direct CSM implementation first if enabled
            if self.use_direct_csm:
                try:
                    logger.info("Loading Direct CSM implementation")
                    # Use the CSM path from config
                    sys.path.append(config.DIRECT_CSM_PATH)
                    self.direct_csm = create_direct_csm(model_path=self.model_path, device=device)
                    self.direct_csm.initialize()
                    logger.info("Direct CSM implementation loaded successfully")
                    return True
                except DirectCSMError as e:
                    logger.warning(f"Failed to load Direct CSM implementation: {e}")
                    logger.info("Falling back to standard CSM model")
                    self.direct_csm = None
            
            # If direct CSM failed or is disabled, use the standard CSM model
            # Create the CSM model - never use placeholder
            self.model = create_csm_model(
                model_path=self.model_path,
                device=device,
                use_placeholder=False  # Never use placeholder
            )
            
            logger.info("CSM model loaded successfully on device: %s", device)
            return True
            
        except Exception as e:
            logger.error("Failed to load CSM model on %s: %s", device, str(e))
            
            # If CUDA failed and we weren't explicitly asked for CPU, try CPU
            if device != "cpu" and (device == "cuda" or device == "auto"):
                logger.info("Attempting to load model on CPU as fallback")
                try:
                    # Try loading direct CSM on CPU if enabled
                    if self.use_direct_csm:
                        try:
                            logger.info("Loading Direct CSM implementation on CPU")
                            self.direct_csm = create_direct_csm(model_path=self.model_path, device="cpu")
                            self.direct_csm.initialize()
                            logger.info("Direct CSM implementation loaded successfully on CPU")
                            return True
                        except DirectCSMError as e:
                            logger.warning(f"Failed to load Direct CSM implementation on CPU: {e}")
                            logger.info("Falling back to standard CSM model on CPU")
                            self.direct_csm = None
                    
                    # Try loading on CPU instead
                    self.model = create_csm_model(
                        model_path=self.model_path,
                        device="cpu",
                        use_placeholder=False  # Never use placeholder
                    )
                    logger.info("CSM model loaded successfully on CPU")
                    return True
                except Exception as cpu_e:
                    logger.error("Failed to load CSM model on CPU fallback: %s", str(cpu_e))
                    # Both GPU and CPU failed, just fail
                    raise RuntimeError(f"Could not load CSM model on any device")
            
            # If we requested CPU specifically and it failed, or if we've already tried fallback, just fail
            raise RuntimeError(f"Could not load CSM model: {e}")
    
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
            device: Device to use for inference ('auto', 'cuda', or 'cpu')
            
        Returns:
            Tuple containing:
                - Path to the generated audio file (or None if failed)
                - URL to access the file (or None if failed)
        """
        # Ensure model is loaded with the specified device
        if not self.is_initialized():
            if not self.load_model(device=device):
                logger.error("Failed to load model")
                return None, None
        
        # Generate a unique filename
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        filename = f"voice_{timestamp}_{unique_id}.wav"
        output_path = os.path.join(self.output_dir, filename)
        
        try:
            logger.info(f"Generating voice for text: '{text}' with speaker_id={speaker_id}, "
                       f"temperature={temperature}, top_k={top_k}, device={device}")
            
            # Try direct CSM first if available
            if self.direct_csm is not None:
                try:
                    # Generate speech using direct CSM
                    audio, sample_rate = self.direct_csm.generate_speech(
                        text=text,
                        speaker_id=speaker_id,
                        temperature=temperature,
                        top_k=top_k,
                        device=device
                    )
                    
                    # Save the audio
                    self.direct_csm.save_audio(audio, sample_rate, output_path)
                    
                    # Check if file was created
                    if not os.path.exists(output_path):
                        logger.error(f"Output file not created: {output_path}")
                        raise DirectCSMError("Output file not created")
                    
                    # Create URL for accessing the file
                    # Use relative path from output_dir to create URL
                    relative_path = os.path.relpath(output_path, self.output_dir)
                    url = f"/voices/{relative_path}"
                    
                    logger.info(f"Voice generated successfully with Direct CSM: {output_path}")
                    return output_path, url
                    
                except DirectCSMError as e:
                    logger.warning(f"Direct CSM failed: {e}, falling back to standard CSM model")
                    # Fall back to standard CSM model
            
            # If direct CSM failed or is not available, use the standard CSM model
            if self.model is not None:
                # Generate speech
                audio, sample_rate = self.model.generate_speech(
                    text=text,
                    speaker_id=speaker_id,
                    temperature=temperature,
                    top_k=top_k,
                    device=device
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
                
                logger.info(f"Voice generated successfully with standard CSM: {output_path}")
                return output_path, url
            else:
                logger.error("No model available for voice generation")
                return None, None
            
        except Exception as e:
            logger.error(f"Error generating voice: {e}")
            
            # Try again with CPU if we were using CUDA and it failed
            if device == "cuda" or device == "auto":
                logger.info("Attempting to fall back to CPU after error")
                try:
                    # Try direct CSM on CPU if available
                    if self.direct_csm is not None:
                        try:
                            # Generate speech using direct CSM on CPU
                            audio, sample_rate = self.direct_csm.generate_speech(
                                text=text,
                                speaker_id=speaker_id,
                                temperature=temperature,
                                top_k=top_k,
                                device="cpu"
                            )
                            
                            # Save the audio
                            self.direct_csm.save_audio(audio, sample_rate, output_path)
                            
                            # Check if file was created
                            if not os.path.exists(output_path):
                                logger.error(f"Output file not created: {output_path}")
                                raise DirectCSMError("Output file not created")
                            
                            # Create URL for accessing the file
                            relative_path = os.path.relpath(output_path, self.output_dir)
                            url = f"/voices/{relative_path}"
                            
                            logger.info(f"Voice generated successfully with Direct CSM on CPU: {output_path}")
                            return output_path, url
                            
                        except DirectCSMError as cpu_e:
                            logger.warning(f"Direct CSM on CPU failed: {cpu_e}, falling back to standard CSM model on CPU")
                    
                    # If direct CSM failed or is not available, use the standard CSM model on CPU
                    if self.model is not None:
                        # Generate speech on CPU
                        audio, sample_rate = self.model.generate_speech(
                            text=text,
                            speaker_id=speaker_id,
                            temperature=temperature,
                            top_k=top_k,
                            device="cpu"
                        )
                        
                        # Save the audio
                        self.model.save_audio(audio, sample_rate, output_path)
                        
                        # Check if file was created
                        if not os.path.exists(output_path):
                            logger.error(f"Output file not created: {output_path}")
                            return None, None
                        
                        # Create URL for accessing the file
                        relative_path = os.path.relpath(output_path, self.output_dir)
                        url = f"/voices/{relative_path}"
                        
                        logger.info(f"Voice generated successfully with standard CSM on CPU: {output_path}")
                        return output_path, url
                    else:
                        logger.error("No model available for voice generation on CPU")
                        return None, None
                    
                except Exception as cpu_e:
                    logger.error(f"Error generating voice on CPU: {cpu_e}")
                    return None, None
            
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
    
    def cleanup(self) -> None:
        """
        Clean up resources used by the voice generator.
        
        This method should be called when shutting down the application or
        when reloading the model with different settings.
        """
        logger.info("Cleaning up voice generator resources")
        
        # Clean up direct CSM if it exists
        if self.direct_csm is not None:
            try:
                self.direct_csm.cleanup()
            except Exception as e:
                logger.warning(f"Error cleaning up direct CSM: {e}")
            self.direct_csm = None
        
        # Clean up standard CSM model if it exists
        if self.model is not None:
            # The standard CSM model doesn't have a cleanup method,
            # so we just set it to None to allow garbage collection
            self.model = None
        
        logger.info("Voice generator resources cleaned up")
    
    def shutdown(self) -> None:
        """
        Shutdown the voice generator.
        
        This is an alias for cleanup for compatibility.
        """
        return self.cleanup()

    def generate_voice(
        self,
        text: str,
        speaker_id: int = config.DEFAULT_SPEAKER_ID,
        temperature: float = config.DEFAULT_TEMPERATURE,
        top_k: int = config.DEFAULT_TOP_K,
        style: str = config.DEFAULT_STYLE,
        device: str = "cuda",
        reload_model: bool = False
    ) -> str:
        """
        Generate voice from text and return the output file path.
        
        This is a simplified version of the generate method that returns only the file path.
        
        Args:
            text: Text to convert to speech
            speaker_id: Speaker ID to use
            temperature: Temperature for sampling (higher = more diverse)
            top_k: Number of highest probability tokens to consider
            style: Voice style to use (not used in current CSM implementation)
            device: Device to use for inference ('cuda' or 'cpu')
            reload_model: Whether to reload the model before generation
            
        Returns:
            Path to the generated audio file (or None if failed)
        """
        # If reload_model is True, unload the model first
        if reload_model and self.is_initialized():
            logger.info("Reloading model as requested")
            self.model = None
            self.direct_csm = None
        
        # Generate the voice using the existing method
        output_path, _ = self.generate(
            text=text,
            speaker_id=speaker_id,
            temperature=temperature,
            top_k=top_k,
            style=style,
            device=device
        )
        
        return output_path


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