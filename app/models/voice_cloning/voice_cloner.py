"""
Voice Cloner module for EchoForge.

This module provides functionality for cloning voices using CSM voice cloning technology.
"""

import os
import logging
import torch
import torchaudio
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union

from app.core import config
from app.models.voice_cloning.csm_integration import CSMVoiceCloner

# Setup logging
logger = logging.getLogger("echoforge.voice_cloner")

class VoiceCloner:
    """
    Voice Cloner for synthesizing speech that sounds like a specific voice.
    
    This class uses the CSM-1B model for high-quality voice cloning,
    similar to the approach used in ElevenLabs.
    """
    
    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize the Voice Cloner.
        
        Args:
            model_path: Path to the cloner model checkpoint
            device: Device to use for inference ('cuda' or 'cpu')
        """
        self.model_path = model_path or config.VOICE_CLONER_MODEL_PATH
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.csm_cloner = CSMVoiceCloner(device=self.device)
        self.is_initialized = False
        
        logger.info(f"Initializing Voice Cloner on device: {self.device}")
    
    def initialize(self) -> bool:
        """
        Initialize the Voice Cloner.
        
        This method initializes the CSM voice cloning system.
        
        Returns:
            True if initialization was successful, False otherwise.
        """
        try:
            if not self.csm_cloner.is_initialized:
                if not self.csm_cloner.initialize():
                    logger.error("Failed to initialize CSM Voice Cloner")
                    return False
            
            self.is_initialized = True
            logger.info("Voice Cloner initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Voice Cloner: {e}")
            return False
    
    def clone_voice(self, text: str, reference_audio: str, 
                   temperature: float = 0.6, top_k: int = 20,
                   transcription: Optional[str] = None,
                   output_path: Optional[str] = None) -> Tuple[torch.Tensor, int]:
        """
        Clone a voice based on reference audio.
        
        Args:
            text: Text to convert to speech
            reference_audio: Path to reference audio file of the voice to clone
            temperature: Temperature for sampling (lower = more consistent)
            top_k: Number of highest probability tokens to consider
            transcription: Optional transcription of the reference audio
            output_path: Optional path to save the generated audio
            
        Returns:
            Tuple containing:
                - Generated audio tensor
                - Sample rate
        """
        if not self.is_initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize Voice Cloner")
        
        try:
            # Use the CSM voice cloning implementation
            audio, sample_rate = self.csm_cloner.clone_voice(
                text=text,
                reference_audio_path=reference_audio,
                transcription=transcription,
                output_path=output_path,
                temperature=temperature,
                top_k=top_k
            )
            
            return audio, sample_rate
        except Exception as e:
            logger.error(f"Error cloning voice: {e}")
            raise
    
    def save_cloned_audio(self, audio: torch.Tensor, sample_rate: int, output_path: str) -> str:
        """
        Save cloned audio to a file.
        
        Args:
            audio: Audio tensor
            sample_rate: Sample rate
            output_path: Path to save the audio
            
        Returns:
            Path to the saved audio file
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            # Ensure audio tensor is properly formatted (unsqueeze to add batch dimension and move to CPU)
            if len(audio.shape) == 1:
                audio = audio.unsqueeze(0)
            audio = audio.cpu()
            torchaudio.save(output_path, audio, sample_rate)
            logger.info(f"Saved cloned audio to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving cloned audio: {e}")
            raise
    
    def clone_from_profile(self, text: str, profile_id: str,
                          temperature: float = 0.6, top_k: int = 20,
                          output_path: Optional[str] = None) -> Tuple[torch.Tensor, int]:
        """
        Clone a voice based on a saved voice profile.
        
        Args:
            text: Text to convert to speech
            profile_id: ID of the voice profile to use
            temperature: Temperature for sampling
            top_k: Number of highest probability tokens to consider
            output_path: Optional path to save the generated audio
            
        Returns:
            Tuple containing:
                - Generated audio tensor
                - Sample rate
        """
        if not self.is_initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize Voice Cloner")
        
        try:
            # Use the CSM voice cloning implementation with a saved profile
            audio, sample_rate = self.csm_cloner.generate_from_profile(
                text=text,
                profile_id=profile_id,
                output_path=output_path,
                temperature=temperature,
                top_k=top_k
            )
            
            return audio, sample_rate
        except Exception as e:
            logger.error(f"Error cloning voice from profile: {e}")
            raise
    
    def cleanup(self):
        """Clean up resources."""
        # Clean up CSM voice cloner resources
        if self.csm_cloner is not None:
            self.csm_cloner.cleanup()
            
        self.is_initialized = False
        logger.info("Voice Cloner cleaned up successfully")
