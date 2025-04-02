"""
CSM Voice Cloning Integration for EchoForge.

This module provides an integration layer between EchoForge and the CSM Voice Cloning code.
"""

import os
import logging
import torch
import torchaudio
import numpy as np
import sys
import whisper
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union
from dataclasses import dataclass

from app.core import config

# Add CSM voice cloning directory to path
CSM_VOICE_CLONING_DIR = Path(__file__).parent.parent.parent.parent / "csm-voice-cloning"
sys.path.append(str(CSM_VOICE_CLONING_DIR))

# Import CSM voice cloning modules
try:
    from generator import load_csm_1b, Segment
    from huggingface_hub import hf_hub_download
except ImportError as e:
    logging.error(f"Failed to import CSM voice cloning modules: {e}")
    raise

# Setup logging
logger = logging.getLogger("echoforge.csm_integration")

class CSMVoiceCloner:
    """
    Integration with CSM Voice Cloning.
    
    This class provides methods to use the CSM-1B model for voice cloning
    within the EchoForge application.
    """
    
    def __init__(self, hf_token: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize the CSM Voice Cloner.
        
        Args:
            hf_token: Hugging Face token for downloading models
            device: Device to use for inference ('cuda' or 'cpu')
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.generator = None
        self.is_initialized = False
        self.whisper_model = None
        self.sample_rate = 24000  # CSM model sample rate
        
        # Set HF token if provided
        if hf_token:
            os.environ["HF_TOKEN"] = hf_token
        
        logger.info(f"Initializing CSM Voice Cloner on device: {self.device}")
    
    def initialize(self) -> bool:
        """
        Initialize the CSM Voice Cloner.
        
        This method downloads and loads the CSM-1B model.
        
        Returns:
            True if initialization was successful, False otherwise.
        """
        try:
            # Download the model if not already cached
            model_path = hf_hub_download(repo_id="sesame/csm-1b", filename="ckpt.pt")
            
            # Load the model
            self.generator = load_csm_1b(model_path, self.device)
            
            # Load the whisper model for transcription
            self.whisper_model = whisper.load_model("base")
            
            self.is_initialized = True
            logger.info("CSM Voice Cloner initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize CSM Voice Cloner: {e}")
            return False
    
    def preprocess_audio(self, audio_path: str) -> Tuple[torch.Tensor, int]:
        """
        Preprocess an audio file for voice cloning.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Tuple of (preprocessed audio tensor, sample rate)
        """
        try:
            # Load audio file
            waveform, sr = torchaudio.load(audio_path)
            waveform = waveform.mean(dim=0)  # Convert to mono
            
            # Resample if needed
            if sr != self.sample_rate:
                waveform = torchaudio.functional.resample(
                    waveform, orig_freq=sr, new_freq=self.sample_rate
                )
            
            # Normalize audio volume
            waveform = waveform / (torch.max(torch.abs(waveform)) + 1e-8)
            
            return waveform, self.sample_rate
        except Exception as e:
            logger.error(f"Error preprocessing audio: {e}")
            raise
    
    def remove_silence(self, audio: torch.Tensor, threshold: float = 0.01, 
                       min_silence_duration: float = 0.2) -> torch.Tensor:
        """
        Remove silence from audio while preserving speech segments.
        
        Args:
            audio: Audio tensor
            threshold: Amplitude threshold for silence detection
            min_silence_duration: Minimum silence duration in seconds
            
        Returns:
            Audio tensor with silence removed
        """
        try:
            # Convert to numpy for easier processing
            audio_np = audio.cpu().numpy()
            
            # Calculate energy
            energy = np.abs(audio_np)
            
            # Find regions above threshold (speech)
            is_speech = energy > threshold
            
            # Convert min_silence_duration to samples
            min_silence_samples = int(min_silence_duration * self.sample_rate)
            
            # Find speech segments
            speech_segments = []
            in_speech = False
            speech_start = 0
            
            for i in range(len(is_speech)):
                if is_speech[i] and not in_speech:
                    # Start of speech segment
                    in_speech = True
                    speech_start = i
                elif not is_speech[i] and in_speech:
                    # Potential end of speech segment
                    # Only end if silence is long enough
                    silence_count = 0
                    for j in range(i, min(len(is_speech), i + min_silence_samples)):
                        if not is_speech[j]:
                            silence_count += 1
                        else:
                            break
                    
                    if silence_count >= min_silence_samples:
                        # End of speech segment
                        in_speech = False
                        speech_segments.append((speech_start, i))
            
            # Handle case where audio ends during speech
            if in_speech:
                speech_segments.append((speech_start, len(is_speech)))
            
            # If no speech found, return original audio
            if not speech_segments:
                return audio
            
            # Add small buffer around segments
            buffer_samples = int(0.05 * self.sample_rate)  # 50ms buffer
            processed_segments = []
            
            for start, end in speech_segments:
                buffered_start = max(0, start - buffer_samples)
                buffered_end = min(len(audio_np), end + buffer_samples)
                processed_segments.append(audio_np[buffered_start:buffered_end])
            
            # Concatenate all segments
            processed_audio = np.concatenate(processed_segments)
            
            return torch.tensor(processed_audio, device=audio.device)
        except Exception as e:
            logger.error(f"Error removing silence: {e}")
            return audio
    
    def _try_cuda_recovery(self):
        """Attempt to recover from CUDA errors by cleaning up and reloading models."""
        logger.info("Attempting CUDA error recovery procedure")
        try:
            # First cleanup existing models
            if hasattr(self, 'whisper_model'):
                if hasattr(self.whisper_model, 'to'):
                    self.whisper_model.to('cpu')
                del self.whisper_model
                self.whisper_model = None
            
            # Aggressively clear CUDA cache
            torch.cuda.empty_cache()
            import gc
            gc.collect()
            
            # Try device reset for extreme cases
            if torch.cuda.is_available():
                device_id = torch.cuda.current_device()
                torch.cuda.device(device_id).empty_cache()
            
            logger.info("CUDA recovery: Memory cleared, will reload models")
            
            # Wait a moment for GPU to stabilize
            import time
            time.sleep(1)
            
            # Reload whisper model on CPU first, then move to device
            self.whisper_model = whisper.load_model("base", device="cpu")
            self.whisper_model = self.whisper_model.to(self.device)
            
            logger.info("CUDA recovery: Models reloaded successfully")
            return True
        except Exception as e:
            logger.error(f"CUDA recovery failed: {e}")
            return False

    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio using Whisper.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcription of the audio
        """
        if not self.is_initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize CSM Voice Cloner")
        
        try:
            try:
                result = self.whisper_model.transcribe(audio_path)
            except RuntimeError as e:
                # Check if this is a CUDA error
                if "CUDA error" in str(e):
                    logger.warning(f"CUDA error during transcription: {e}")
                    logger.warning("Attempting to recover from CUDA error...")
                    
                    # Try to recover
                    if self._try_cuda_recovery():
                        # Try again with the reloaded model
                        result = self.whisper_model.transcribe(audio_path)
                    else:
                        # If recovery failed, try running on CPU as a fallback
                        logger.warning("CUDA recovery failed, attempting to run on CPU instead")
                        cpu_model = whisper.load_model("base", device="cpu")
                        result = cpu_model.transcribe(audio_path)
                else:
                    # Not a CUDA error, re-raise
                    raise
                    
            transcription = result["text"].strip()
            logger.info(f"Transcribed audio: {transcription[:50]}...")
            return transcription
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            # Try to cleanup after an error
            try:
                torch.cuda.empty_cache()
            except:
                pass
            raise
    
    def clone_voice(self, text: str, reference_audio_path: str, transcription: Optional[str] = None,
                   output_path: Optional[str] = None, speaker_id: int = 999,
                   temperature: float = 0.6, top_k: int = 20,
                   max_audio_length_ms: int = 15000) -> Tuple[torch.Tensor, int]:
        """
        Clone a voice based on reference audio.
        
        Args:
            text: Text to convert to speech
            reference_audio_path: Path to reference audio file of the voice to clone
            transcription: Optional transcription of reference audio (will auto-transcribe if not provided)
            output_path: Optional path to save the generated audio
            speaker_id: Speaker ID to use
            temperature: Temperature for sampling
            top_k: Number of highest probability tokens to consider
            max_audio_length_ms: Maximum audio length in milliseconds
            
        Returns:
            Tuple containing:
                - Generated audio tensor
                - Sample rate
        """
        if not self.is_initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize CSM Voice Cloner")
        
        # Clear CUDA cache before starting to help prevent memory fragmentation
        torch.cuda.empty_cache()
        
        try:
            # Process reference audio
            context_audio, _ = self.preprocess_audio(reference_audio_path)
            
            # Get audio duration
            audio_duration_sec = len(context_audio) / self.sample_rate
            logger.info(f"Original audio duration: {audio_duration_sec:.2f} seconds")
            
            # Adjust threshold based on audio length
            silence_threshold = 0.015
            if audio_duration_sec > 10:
                # For longer files, be more aggressive with silence removal
                silence_threshold = 0.02
            
            # Remove silence
            context_audio = self.remove_silence(
                context_audio, 
                threshold=silence_threshold,
                min_silence_duration=0.15
            )
            
            # Get processed audio duration
            processed_duration_sec = len(context_audio) / self.sample_rate
            logger.info(f"Processed audio duration: {processed_duration_sec:.2f} seconds")
            
            # Get transcription if not provided
            if transcription is None or transcription.strip() == "":
                transcription = self.transcribe_audio(reference_audio_path)
            
            # Create context segment
            context_segment = Segment(
                text=transcription,
                speaker=speaker_id,
                audio=context_audio
            )
            
            # Preprocess text for better pronunciation
            # Add punctuation if missing to help with phrasing
            if not any(p in text for p in ['.', ',', '!', '?']):
                text = text + '.'
            
            # Generate audio with context
            audio = self.generator.generate(
                text=text,
                speaker=speaker_id,
                context=[context_segment],
                max_audio_length_ms=max_audio_length_ms,
                temperature=temperature,
                topk=top_k
                # Removed max_seq_len parameter that was causing errors
            )
            
            # Save the audio if output_path is provided
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                torchaudio.save(output_path, audio.unsqueeze(0).cpu(), self.generator.sample_rate)
                logger.info(f"Audio saved to {output_path}")
            
            return audio, self.generator.sample_rate
        except Exception as e:
            logger.error(f"Error cloning voice: {e}")
            raise
    
    def save_profile(self, profile_id: str, reference_audio_path: str, 
                    transcription: Optional[str] = None) -> Dict[str, Any]:
        """
        Save a voice profile for future use.
        
        Args:
            profile_id: Unique identifier for the voice profile
            reference_audio_path: Path to reference audio
            transcription: Optional transcription of reference audio
            
        Returns:
            Dictionary containing profile information
        """
        try:
            # Create profiles directory if it doesn't exist
            profiles_dir = Path(config.VOICE_PROFILES_DIR)
            profiles_dir.mkdir(parents=True, exist_ok=True)
            
            # Preprocess audio
            audio, _ = self.preprocess_audio(reference_audio_path)
            
            # Remove silence
            audio = self.remove_silence(audio)
            
            # Get transcription if not provided
            if transcription is None or transcription.strip() == "":
                transcription = self.transcribe_audio(reference_audio_path)
            
            # Create profile directory
            profile_dir = profiles_dir / profile_id
            profile_dir.mkdir(exist_ok=True)
            
            # Save audio
            audio_path = profile_dir / "reference.wav"
            torchaudio.save(audio_path, audio.unsqueeze(0).cpu(), self.sample_rate)
            
            # Save transcription
            with open(profile_dir / "transcription.txt", "w") as f:
                f.write(transcription)
            
            # Save metadata
            profile_info = {
                "profile_id": profile_id,
                "audio_path": str(audio_path),
                "transcription": transcription,
                "sample_rate": self.sample_rate,
                "duration": len(audio) / self.sample_rate
            }
            
            return profile_info
        except Exception as e:
            logger.error(f"Error saving voice profile: {e}")
            raise
    
    def load_profile(self, profile_id: str) -> Dict[str, Any]:
        """
        Load a voice profile.
        
        Args:
            profile_id: Unique identifier for the voice profile
            
        Returns:
            Dictionary containing profile information
        """
        try:
            # Get profile directory
            profile_dir = Path(config.VOICE_PROFILES_DIR) / profile_id
            
            if not profile_dir.exists():
                raise FileNotFoundError(f"Voice profile not found: {profile_id}")
            
            # Load audio
            audio_path = profile_dir / "reference.wav"
            audio, sr = torchaudio.load(audio_path)
            audio = audio.squeeze(0)  # Remove batch dimension
            
            # Load transcription
            with open(profile_dir / "transcription.txt", "r") as f:
                transcription = f.read().strip()
            
            profile_info = {
                "profile_id": profile_id,
                "audio_path": str(audio_path),
                "transcription": transcription,
                "audio": audio,
                "sample_rate": sr,
                "duration": len(audio) / sr
            }
            
            return profile_info
        except Exception as e:
            logger.error(f"Error loading voice profile: {e}")
            raise
    
    def generate_from_profile(self, text: str, profile_id: str, 
                             output_path: Optional[str] = None,
                             speaker_id: int = 999,
                             temperature: float = 0.6, 
                             top_k: int = 20,
                             max_audio_length_ms: int = 15000) -> Tuple[torch.Tensor, int]:
        """
        Generate speech using a saved voice profile.
        
        Args:
            text: Text to convert to speech
            profile_id: ID of the voice profile to use
            output_path: Optional path to save the generated audio
            speaker_id: Speaker ID to use
            temperature: Temperature for sampling
            top_k: Number of highest probability tokens to consider
            max_audio_length_ms: Maximum audio length in milliseconds
            
        Returns:
            Tuple containing:
                - Generated audio tensor
                - Sample rate
        """
        if not self.is_initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize CSM Voice Cloner")
        
        try:
            # Load profile
            profile = self.load_profile(profile_id)
            
            # Create context segment
            context_segment = Segment(
                text=profile["transcription"],
                speaker=speaker_id,
                audio=profile["audio"].to(self.device)
            )
            
            # Preprocess text for better pronunciation
            if not any(p in text for p in ['.', ',', '!', '?']):
                text = text + '.'
            
            # Generate audio with context
            audio = self.generator.generate(
                text=text,
                speaker=speaker_id,
                context=[context_segment],
                max_audio_length_ms=max_audio_length_ms,
                temperature=temperature,
                topk=top_k,
            )
            
            # Save the audio if output_path is provided
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                torchaudio.save(output_path, audio.unsqueeze(0).cpu(), self.generator.sample_rate)
                logger.info(f"Audio saved to {output_path}")
            
            return audio, self.generator.sample_rate
        except Exception as e:
            logger.error(f"Error generating speech from profile: {e}")
            raise
    
    def cleanup(self):
        """Clean up resources and free GPU memory."""
        # Log cleanup attempt
        logger.info("Cleaning up CSM Voice Cloner resources")
        
        # First delete the models
        if hasattr(self, 'generator') and self.generator is not None:
            try:
                # Move generator to CPU before deletion to help with CUDA memory recovery
                if hasattr(self.generator, 'to'):
                    self.generator.to('cpu')
                # Explicitly delete the generator
                del self.generator
                self.generator = None
                logger.info("Generator model deleted")
            except Exception as e:
                logger.error(f"Error deleting generator: {e}")
                
        if hasattr(self, 'whisper_model') and self.whisper_model is not None:
            try:
                # Move whisper model to CPU before deletion
                if hasattr(self.whisper_model, 'to'):
                    self.whisper_model.to('cpu')
                # Explicitly delete the whisper model
                del self.whisper_model
                self.whisper_model = None
                logger.info("Whisper model deleted")
            except Exception as e:
                logger.error(f"Error deleting whisper model: {e}")
                
        # Clear all cached variables that might hold tensors
        try:
            # Delete all attributes that might contain tensors
            for attr in dir(self):
                if attr.startswith('_'):
                    continue
                if hasattr(self, attr):
                    attr_value = getattr(self, attr)
                    if isinstance(attr_value, torch.Tensor):
                        try:
                            # Move tensor to CPU first
                            if attr_value.is_cuda:
                                attr_value = attr_value.cpu()
                            # Delete the attribute
                            delattr(self, attr)
                            logger.info(f"Deleted tensor attribute: {attr}")
                        except Exception as e:
                            logger.error(f"Error deleting tensor attribute {attr}: {e}")
        except Exception as e:
            logger.error(f"Error during tensor cleanup: {e}")

        # Aggressively clear CUDA cache
        try:
            # Empty CUDA cache
            torch.cuda.empty_cache()
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # For extreme cases, try to reset the CUDA device
            if torch.cuda.is_available():
                device_id = torch.cuda.current_device()
                torch.cuda.device(device_id).empty_cache()
                logger.info(f"Reset CUDA device {device_id}")
                
            logger.info("CUDA memory cache cleared")
        except Exception as e:
            logger.error(f"Error clearing CUDA cache: {e}")
        
        # Force garbage collection
        try:
            import gc
            gc.collect()
            logger.info("Garbage collection completed")
        except Exception as e:
            logger.error(f"Error during garbage collection: {e}")
        
        # Clear CUDA cache if available
        if torch.cuda.is_available():
            try:
                # Empty CUDA cache
                torch.cuda.empty_cache()
                logger.info("CUDA cache cleared")
                
                # Reset peak memory stats
                torch.cuda.reset_peak_memory_stats()
                logger.info("CUDA peak memory stats reset")
            except Exception as e:
                logger.error(f"Error clearing CUDA cache: {e}")
        
        # Reset initialization flag
        self.is_initialized = False
        self.generator = None
        self.whisper_model = None
        
        logger.info("CSM Voice Cloner cleaned up successfully")
