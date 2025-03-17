"""
Direct CSM Implementation

This module provides a direct implementation of the CSM (Conversational Speech Model) for voice generation.
It bypasses the adapter layers and directly uses the CSM model from the tts_poc/voice_poc/csm directory.
"""

import os
import sys
import logging
import time
import torch
import torchaudio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

# Set up logging
logger = logging.getLogger("echoforge.direct_csm")

# Add the CSM directory to the path
CSM_PATH = "/home/tdeshane/tts_poc/voice_poc/csm"
sys.path.append(CSM_PATH)

# Output directory
OUTPUT_DIR = "/tmp/echoforge/voices/generated"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class DirectCSMError(Exception):
    """Base exception for Direct CSM errors."""
    pass

class DirectCSMNotFoundError(DirectCSMError):
    """Exception raised when the CSM model cannot be found."""
    pass

class DirectCSMLoadError(DirectCSMError):
    """Exception raised when the CSM model cannot be loaded."""
    pass

class DirectCSM:
    """
    Direct implementation of the CSM (Conversational Speech Model) for voice generation.
    
    This class bypasses the adapter layers and directly uses the CSM model from the
    tts_poc/voice_poc/csm directory.
    """
    
    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize the Direct CSM implementation.
        
        Args:
            model_path: Path to the model checkpoint. If None, will try to find it automatically.
            device: Device to use for inference ('cuda' or 'cpu'). If None, will use CUDA if available.
        """
        self.model_path = model_path
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        self.generator = None
        self.is_initialized = False
        
        logger.info(f"DirectCSM initialized with device={self.device}")
    
    def initialize(self) -> bool:
        """
        Initialize the CSM model.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        if self.is_initialized:
            logger.info("DirectCSM already initialized")
            return True
        
        try:
            # Import the CSM generator
            try:
                from generator import load_csm_1b
                logger.info("Successfully imported CSM modules")
            except ImportError as e:
                logger.error(f"Error importing CSM modules: {e}")
                logger.error(f"Make sure the CSM code is available at: {CSM_PATH}")
                raise DirectCSMNotFoundError(f"Could not import CSM modules: {e}")
            
            # Find the model checkpoint if not provided
            if not self.model_path:
                self.model_path = self._find_model_checkpoint()
                
            logger.info(f"Using model checkpoint: {self.model_path}")
            
            # Load the model
            logger.info(f"Loading CSM model on {self.device}...")
            self.generator = load_csm_1b(self.model_path, self.device)
            logger.info("CSM model loaded successfully")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.exception(f"Error initializing DirectCSM: {e}")
            
            # If CUDA failed, try CPU
            if self.device == "cuda":
                logger.info("Attempting to initialize on CPU after CUDA failure")
                self.device = "cpu"
                try:
                    from generator import load_csm_1b
                    self.generator = load_csm_1b(self.model_path, self.device)
                    logger.info("CSM model loaded successfully on CPU")
                    self.is_initialized = True
                    return True
                except Exception as cpu_e:
                    logger.exception(f"Error initializing DirectCSM on CPU: {cpu_e}")
            
            raise DirectCSMLoadError(f"Could not initialize DirectCSM: {e}")
    
    def _find_model_checkpoint(self) -> str:
        """
        Find the CSM model checkpoint.
        
        Returns:
            str: Path to the model checkpoint.
            
        Raises:
            DirectCSMNotFoundError: If the model checkpoint cannot be found.
        """
        # Try the default location
        default_path = os.path.join(CSM_PATH, "ckpt.pt")
        if os.path.exists(default_path):
            return default_path
        
        # Try the Hugging Face cache
        hf_cache = os.path.expanduser("~/.cache/huggingface/hub")
        for root, dirs, files in os.walk(hf_cache):
            if "ckpt.pt" in files:
                return os.path.join(root, "ckpt.pt")
        
        raise DirectCSMNotFoundError("Could not find CSM model checkpoint")
    
    def generate_speech(
        self,
        text: str,
        speaker_id: int = 1,
        temperature: float = 0.9,
        top_k: int = 50,
        max_audio_length_ms: float = 90000,
        device: Optional[str] = None
    ) -> Tuple[torch.Tensor, int]:
        """
        Generate speech from text using the CSM model directly.
        
        Args:
            text: Text to convert to speech.
            speaker_id: Speaker ID to use.
            temperature: Temperature for sampling (higher = more diverse).
            top_k: Number of highest probability tokens to consider.
            max_audio_length_ms: Maximum audio length in milliseconds.
            device: Device to use for inference ('cuda' or 'cpu'). If None, will use the device specified at initialization.
            
        Returns:
            Tuple containing:
                - The generated audio tensor
                - The sample rate
                
        Raises:
            DirectCSMError: If speech generation fails.
        """
        # Initialize if not already initialized
        if not self.is_initialized:
            logger.info("DirectCSM not initialized, initializing now")
            self.initialize()
        
        # Update device if specified
        if device and device != self.device:
            logger.info(f"Switching device from {self.device} to {device}")
            self.device = device
            # Re-initialize with the new device
            self.is_initialized = False
            self.initialize()
        
        try:
            logger.info(f"Generating speech for text: '{text}'")
            
            start_time = time.time()
            audio = self.generator.generate(
                text=text,
                speaker=speaker_id,
                context=[],
                temperature=temperature,
                topk=top_k,
                max_audio_length_ms=max_audio_length_ms
            )
            generation_time = time.time() - start_time
            
            logger.info(f"Speech generated in {generation_time:.2f} seconds")
            
            # Get the sample rate from the generator
            sample_rate = getattr(self.generator, 'sample_rate', 24000)
            
            return audio, sample_rate
            
        except Exception as e:
            logger.exception(f"Error generating speech: {e}")
            
            # If CUDA failed, try CPU
            if self.device == "cuda":
                logger.info("Attempting to generate on CPU after CUDA failure")
                self.device = "cpu"
                try:
                    # Re-initialize with CPU
                    self.is_initialized = False
                    self.initialize()
                    
                    # Try again with CPU
                    start_time = time.time()
                    audio = self.generator.generate(
                        text=text,
                        speaker=speaker_id,
                        context=[],
                        temperature=temperature,
                        topk=top_k,
                        max_audio_length_ms=max_audio_length_ms
                    )
                    generation_time = time.time() - start_time
                    
                    logger.info(f"Speech generated on CPU in {generation_time:.2f} seconds")
                    
                    # Get the sample rate from the generator
                    sample_rate = getattr(self.generator, 'sample_rate', 24000)
                    
                    return audio, sample_rate
                    
                except Exception as cpu_e:
                    logger.exception(f"Error generating speech on CPU: {cpu_e}")
            
            raise DirectCSMError(f"Could not generate speech: {e}")
    
    def save_audio(self, audio: torch.Tensor, sample_rate: int, output_path: str) -> str:
        """
        Save the generated audio to a file.
        
        Args:
            audio: The audio tensor to save.
            sample_rate: The sample rate of the audio.
            output_path: The path to save the audio to.
            
        Returns:
            str: The path to the saved audio file.
            
        Raises:
            DirectCSMError: If the audio cannot be saved.
        """
        try:
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Make sure the audio is on CPU
            if audio.device.type != "cpu":
                audio = audio.cpu()
            
            # Save the audio
            torchaudio.save(output_path, audio.unsqueeze(0), sample_rate)
            
            logger.info(f"Audio saved to {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.exception(f"Error saving audio: {e}")
            raise DirectCSMError(f"Could not save audio: {e}")
    
    def cleanup(self) -> None:
        """
        Clean up resources used by the DirectCSM implementation.
        """
        if hasattr(self, 'generator') and self.generator is not None:
            # Clean up any resources
            self.generator = None
        
        self.is_initialized = False
        logger.info("DirectCSM resources cleaned up")


def create_direct_csm(model_path: Optional[str] = None, device: Optional[str] = None) -> DirectCSM:
    """
    Create a DirectCSM instance.
    
    Args:
        model_path: Path to the model checkpoint. If None, will try to find it automatically.
        device: Device to use for inference ('cuda' or 'cpu'). If None, will use CUDA if available.
        
    Returns:
        DirectCSM: A DirectCSM instance.
    """
    return DirectCSM(model_path=model_path, device=device) 