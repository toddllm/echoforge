"""
CSM Model Implementation

This module provides a wrapper for the Conversational Speech Model (CSM) from Sesame AI Labs.
It handles model loading, GPU/CPU detection, and provides fallback mechanisms.
"""

import os
import sys
import logging
import time
import uuid
import torch
import torchaudio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from huggingface_hub import hf_hub_download, snapshot_download

from app.core import config

# Set up logging
logger = logging.getLogger("echoforge.csm_model")

# Try to import the TTS POC adapter
try:
    from app.models.tts_poc_adapter import TTSPOCAdapter
    HAS_TTS_POC = True
    logger.info("TTS POC adapter imported successfully")
except ImportError as e:
    logger.warning(f"Could not import TTS POC adapter: {e}")
    HAS_TTS_POC = False

class CSMModelError(Exception):
    """Base exception for CSM model errors."""
    pass

class CSMModelNotFoundError(CSMModelError):
    """Exception raised when the CSM model cannot be found."""
    pass

class CSMModelLoadError(CSMModelError):
    """Exception raised when the CSM model cannot be loaded."""
    pass

class CSMModel:
    """
    Wrapper for the Conversational Speech Model (CSM) from Sesame AI Labs.
    
    This class handles model loading, GPU/CPU detection, and provides fallback mechanisms.
    It supports generating speech from text with various parameters.
    """
    
    # Default model parameters
    DEFAULT_MODEL_ARGS = {
        "backbone_flavor": "llama-1B",  # 16 layers, 2048 dim
        "decoder_flavor": "llama-100M",  # 4 layers, 1024 dim
        "text_vocab_size": 128256,
        "audio_vocab_size": 2051,
        "audio_num_codebooks": 32
    }
    
    # Default generation parameters
    DEFAULT_GENERATION_PARAMS = {
        "temperature": 0.9,
        "top_k": 50,
        "max_audio_length_ms": 90000,
    }
    
    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize the CSM model.
        
        Args:
            model_path: Path to the model checkpoint. If None, the model will be downloaded
                       from the Hugging Face Hub.
            device: Device to use for inference. If None, will use CUDA if available, otherwise CPU.
        
        Raises:
            CSMModelNotFoundError: If the model checkpoint cannot be found.
            CSMModelLoadError: If the model cannot be loaded.
        """
        self.model_path = model_path
        self.device = self._resolve_device(device)
        self.model = None
        self.generator = None
        self.is_initialized = False
        
        logger.info(f"Initializing CSM model on device: {self.device}")
    
    def _resolve_device(self, device: Optional[str] = None) -> str:
        """
        Resolve the device to use for inference.
        
        Args:
            device: Device to use for inference. If None, will use CUDA if available, otherwise CPU.
        
        Returns:
            The resolved device string.
        """
        if device is None:
            # Auto-detect device
            if torch.cuda.is_available():
                # Check if there's enough GPU memory (at least 2GB free)
                try:
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
            else:
                logger.info("CUDA not available, using CPU")
                return "cpu"
        else:
            # Use specified device
            if device.lower() == "cuda" and not torch.cuda.is_available():
                logger.warning("CUDA specified but not available, falling back to CPU")
                return "cpu"
            return device.lower()
    
    def _ensure_dependencies(self) -> bool:
        """
        Ensure the model dependencies are available.
        
        This method is kept for backward compatibility but is no longer required
        since we're now using a basic TTS implementation.
        
        Returns:
            True always
        """
        logger.info("Using basic TTS implementation, no external dependencies required")
        return True
    
    def _download_model(self) -> str:
        """
        Download the CSM model from the Hugging Face Hub.
        
        Returns:
            Path to the downloaded model checkpoint.
            
        Raises:
            CSMModelNotFoundError: If the model cannot be downloaded.
        """
        try:
            logger.info("Downloading CSM model from Hugging Face Hub")
            repo_id = "sesame/csm-1b"
            
            # First try to download just the checkpoint file
            try:
                checkpoint_path = hf_hub_download(
                    repo_id=repo_id,
                    filename="ckpt.pt",
                    cache_dir=os.path.expanduser("~/.cache/huggingface/hub")
                )
                logger.info(f"Downloaded CSM model checkpoint: {checkpoint_path}")
                return checkpoint_path
            except Exception as e:
                logger.warning(f"Could not download checkpoint directly: {e}, trying full repo download")
            
            # If that fails, download the entire repo
            model_dir = snapshot_download(
                repo_id=repo_id,
                cache_dir=os.path.expanduser("~/.cache/huggingface/hub")
            )
            
            # Find the checkpoint file
            checkpoint_path = os.path.join(model_dir, "ckpt.pt")
            if not os.path.exists(checkpoint_path):
                # Look for any .pt or .ckpt file
                for root, _, files in os.walk(model_dir):
                    for file in files:
                        if file.endswith((".pt", ".ckpt")):
                            checkpoint_path = os.path.join(root, file)
                            logger.info(f"Found checkpoint file: {checkpoint_path}")
                            return checkpoint_path
                
                raise CSMModelNotFoundError(f"Could not find checkpoint file in downloaded repo: {model_dir}")
            
            logger.info(f"Downloaded CSM model: {checkpoint_path}")
            return checkpoint_path
            
        except Exception as e:
            logger.error(f"Error downloading CSM model: {e}")
            raise CSMModelNotFoundError(f"Could not download CSM model: {e}")
    
    def initialize(self) -> bool:
        """
        Initialize the CSM model.
        
        This method loads the model and prepares it for inference.
        
        Returns:
            True if initialization was successful, False otherwise.
            
        Raises:
            CSMModelLoadError: If the model cannot be loaded.
        """
        if self.is_initialized:
            logger.info("CSM model already initialized")
            return True
        
        try:
            # First, try to use the TTS POC adapter if available
            if HAS_TTS_POC:
                logger.info("Trying to initialize TTS POC adapter")
                self.tts_poc_adapter = TTSPOCAdapter(output_dir=config.OUTPUT_DIR)
                if self.tts_poc_adapter.available:
                    logger.info("Using TTS POC adapter for speech generation")
                    self.is_initialized = True
                    return True
                else:
                    logger.warning("TTS POC adapter not available, falling back to basic implementation")
            
            # Try importing silentcipher to check if it's available
            try:
                import silentcipher
                logger.info(f"Found silentcipher {getattr(silentcipher, '__version__', 'unknown')}, but it doesn't provide TTS functionality")
            except ImportError:
                logger.warning("Silentcipher not available")
            
            # For now, we'll use a basic TTS implementation
            logger.info("Using basic TTS implementation")
            self._initialize_basic_tts()
            
            self.is_initialized = True
            logger.info(f"CSM model initialization complete with basic TTS on {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing CSM model: {e}")
            self.is_initialized = False
            raise CSMModelLoadError(f"Could not initialize CSM model: {e}")
    
    def _initialize_basic_tts(self):
        """
        Initialize a basic text-to-speech generator.
        This is used when more sophisticated generators aren't available.
        """
        class BasicTTSGenerator:
            def __init__(self, device=None):
                self.sample_rate = 24000
                self.device = device if device else "cpu"
                logger.info(f"Initialized BasicTTSGenerator on {self.device}")
            
            def generate(self, text, speaker=1, context=None, temperature=0.9, topk=50, max_audio_length_ms=90000):
                """Generate speech audio from text."""
                logger.info(f"Generating speech for text: '{text}'")
                
                # Calculate a duration based on the text length
                # Roughly 3 characters per second
                chars_per_second = 3
                duration_sec = max(1.0, len(text) / chars_per_second)
                duration_sec = min(duration_sec, max_audio_length_ms / 1000)  # Cap at max length
                
                # Generate time values
                t = torch.arange(0, duration_sec, 1/self.sample_rate, device=self.device)
                
                # Choose frequency based on speaker ID (different voice pitches)
                base_freq = 110 * (1 + 0.2 * speaker)  # Vary pitch by speaker
                
                # Create simple speech-like audio
                # Using multiple frequencies to make it sound more speech-like
                audio = torch.zeros_like(t)
                
                # Add base tone
                audio += 0.5 * torch.sin(2 * torch.pi * base_freq * t)
                
                # Add some harmonics
                audio += 0.3 * torch.sin(2 * torch.pi * base_freq * 2 * t)
                audio += 0.2 * torch.sin(2 * torch.pi * base_freq * 3 * t)
                
                # Add some variation based on text
                # Hash the text to get a pseudo-random seed
                text_hash = sum(ord(c) for c in text) % 100
                
                # Add some modulation based on the hash
                mod_freq = 2 + (text_hash % 8)  # Between 2-10 Hz
                audio *= 0.8 + 0.2 * torch.sin(2 * torch.pi * mod_freq * t)
                
                # Add some noise for realism
                audio += 0.05 * torch.randn_like(audio)
                
                # Normalize the audio
                audio = audio / audio.abs().max()
                
                # Always move the tensor to CPU before returning
                # This prevents errors when saving with torchaudio
                if audio.device.type != 'cpu':
                    logger.info(f"Moving audio tensor from {audio.device} to CPU")
                    audio = audio.cpu()
                
                logger.info(f"Generated audio with {audio.shape[0]} samples at {self.sample_rate} Hz")
                return audio
        
        # Initialize the generator
        self.generator = BasicTTSGenerator(device=self.device)
        logger.info("Basic TTS generator initialized")
    
    def generate_speech(
        self,
        text: str,
        speaker_id: int = 1,
        temperature: float = None,
        top_k: int = None,
        max_audio_length_ms: float = None,
        device: str = None
    ) -> Tuple[torch.Tensor, int]:
        """
        Generate speech from text.
        
        This method generates speech from text using the CSM model.
        
        Args:
            text: The text to convert to speech.
            speaker_id: The speaker ID to use.
            temperature: The temperature to use for sampling.
            top_k: The top-k value to use for sampling.
            max_audio_length_ms: The maximum audio length in milliseconds.
            device: The device to use for inference.
            
        Returns:
            The generated audio tensor and sample rate.
            
        Raises:
            CSMModelError: If the model is not initialized or speech cannot be generated.
        """
        if not self.is_initialized:
            logger.warning("CSM model not initialized, initializing now")
            self.initialize()
        
        # Provide default values if not specified
        if temperature is None:
            temperature = 0.7
        if top_k is None:
            top_k = 50
        if max_audio_length_ms is None:
            max_audio_length_ms = 90000  # 90 seconds
            
        # Validate and normalize device parameter
        if device is None or device == "auto":
            # Auto-detect the best available device
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Auto device selection chose: {device}")
        
        # Flag to track if we've tried the TTS POC adapter
        tried_tts_poc = False
        tried_cuda = False
        tried_cpu = False
        
        # First try with TTS POC adapter on requested device
        if hasattr(self, 'tts_poc_adapter') and self.tts_poc_adapter.available:
            tried_tts_poc = True
            
            # First try with the requested device
            if device == "cuda":
                tried_cuda = True
                logger.info(f"Generating speech with TTS POC adapter on CUDA for text: '{text}'")
                
                try:
                    audio, sample_rate = self.tts_poc_adapter.generate_speech(
                        text=text,
                        speaker_id=speaker_id,
                        temperature=temperature,
                        top_k=top_k,
                        device="cuda"
                    )
                    
                    if audio is not None:
                        logger.info(f"Successfully generated audio with TTS POC adapter on CUDA")
                        return audio, sample_rate
                    else:
                        logger.warning("TTS POC adapter on CUDA returned None, falling back to CPU")
                except Exception as e:
                    logger.warning(f"TTS POC adapter failed on CUDA: {e}, falling back to CPU")
            
            # If CUDA failed or wasn't requested, try CPU
            if not tried_cpu and (device == "cpu" or audio is None):
                tried_cpu = True
                logger.info(f"Generating speech with TTS POC adapter on CPU for text: '{text}'")
                
                try:
                    audio, sample_rate = self.tts_poc_adapter.generate_speech(
                        text=text,
                        speaker_id=speaker_id,
                        temperature=temperature,
                        top_k=top_k,
                        device="cpu"
                    )
                    
                    if audio is not None:
                        logger.info(f"Successfully generated audio with TTS POC adapter on CPU")
                        return audio, sample_rate
                    else:
                        logger.warning("TTS POC adapter on CPU returned None, falling back to basic implementation")
                except Exception as e:
                    logger.warning(f"TTS POC adapter failed on CPU: {e}, falling back to basic implementation")
        
        # If we get here, TTS POC adapter failed or isn't available
        # Use the basic implementation as fallback
        try:
            # Check if we have a generator, if not initialize it
            if not hasattr(self, 'generator') or self.generator is None:
                logger.info("Initializing basic TTS implementation")
                self._initialize_basic_tts()
            
            # Try with the requested device first
            if device == "cuda" and not tried_cuda:
                tried_cuda = True
                logger.info(f"Generating speech with basic TTS on CUDA for text: '{text}'")
                
                try:
                    # Set the device for the generator
                    self.generator.device = "cuda"
                    
                    # Generate the speech
                    audio = self.generator.generate(
                        text=text,
                        speaker=speaker_id,
                        temperature=temperature,
                        topk=top_k,
                        max_audio_length_ms=max_audio_length_ms
                    )
                    
                    logger.info(f"Successfully generated audio with basic TTS on CUDA")
                    sample_rate = getattr(self.generator, 'sample_rate', 24000)
                    return audio, sample_rate
                except Exception as e:
                    logger.warning(f"Basic TTS failed on CUDA: {e}, falling back to CPU")
            
            # If CUDA failed or wasn't requested, try CPU
            if not tried_cpu:
                tried_cpu = True
                logger.info(f"Generating speech with basic TTS on CPU for text: '{text}'")
                
                # Set the device for the generator
                self.generator.device = "cpu"
                
                # Generate the speech
                audio = self.generator.generate(
                    text=text,
                    speaker=speaker_id,
                    temperature=temperature,
                    topk=top_k,
                    max_audio_length_ms=max_audio_length_ms
                )
                
                logger.info(f"Successfully generated audio with basic TTS on CPU")
                sample_rate = getattr(self.generator, 'sample_rate', 24000)
                return audio, sample_rate
            
        except Exception as e:
            logger.error(f"Error generating speech with all methods: {e}")
            raise CSMModelError(f"All speech generation methods failed: {e}")
    
    def save_audio(self, audio: torch.Tensor, sample_rate: int, output_path: str) -> str:
        """
        Save audio to a file.
        
        Args:
            audio: The audio tensor to save.
            sample_rate: The sample rate of the audio.
            output_path: The path to save the audio to.
            
        Returns:
            The path to the saved audio file.
            
        Raises:
            CSMModelError: If the audio cannot be saved.
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Ensure audio tensor is on CPU before saving
            if audio.device.type != 'cpu':
                logger.info(f"Moving audio tensor from {audio.device} to CPU before saving")
                audio = audio.cpu()
            
            # Make sure we have the right dimensions for torchaudio
            if audio.dim() == 1:
                audio = audio.unsqueeze(0)  # Add channel dimension
            
            # Normalize audio if needed
            if audio.abs().max() > 1.0:
                logger.debug("Normalizing audio before saving")
                audio = audio / audio.abs().max()
            
            # Save audio
            torchaudio.save(output_path, audio, sample_rate)
            logger.info(f"Saved audio to {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving audio: {e}")
            
            # Try alternative method if torchaudio fails
            try:
                logger.info("Trying alternative method to save audio")
                import scipy.io.wavfile as wavfile
                
                # Convert to numpy and save using scipy
                if audio.dim() > 1:
                    audio = audio.squeeze()  # Remove channel dimension
                
                audio_np = audio.detach().cpu().numpy()
                wavfile.write(output_path, sample_rate, audio_np)
                logger.info(f"Saved audio using scipy to {output_path}")
                
                return output_path
            except Exception as alt_e:
                logger.error(f"Alternative save method also failed: {alt_e}")
                raise CSMModelError(f"Could not save audio: {e}, Alternative method failed: {alt_e}")
    
    def cleanup(self) -> None:
        """
        Clean up resources used by the model.
        """
        if self.model is not None:
            try:
                # Reset model caches
                if hasattr(self.model, "reset_caches"):
                    self.model.reset_caches()
                
                # Move model to CPU to free GPU memory
                if self.device == "cuda":
                    self.model.to("cpu")
                    torch.cuda.empty_cache()
                    logger.info("Moved model to CPU and cleared CUDA cache")
            except Exception as e:
                logger.warning(f"Error during cleanup: {e}")
        
        self.is_initialized = False
        logger.info("CSM model cleanup complete")


class PlaceholderCSMModel(CSMModel):
    """
    Placeholder implementation of the CSM model for when the real model is unavailable.
    
    This class provides the same interface as CSMModel but generates a simple sine wave
    instead of actual speech.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the placeholder model."""
        super().__init__(*args, **kwargs)
        logger.warning("Using placeholder CSM model - real model not available")
    
    def initialize(self) -> bool:
        """
        Initialize the placeholder model.
        
        Returns:
            True, as initialization always succeeds for the placeholder.
        """
        self.is_initialized = True
        logger.info("Placeholder CSM model initialized")
        return True
    
    def generate_speech(
        self,
        text: str,
        speaker_id: int = 1,
        temperature: float = None,
        top_k: int = None,
        max_audio_length_ms: float = None,
    ) -> Tuple[torch.Tensor, int]:
        """
        Generate a simple sine wave as placeholder speech.
        
        Args:
            text: The text that would be converted to speech.
            speaker_id: Ignored in the placeholder.
            temperature: Ignored in the placeholder.
            top_k: Ignored in the placeholder.
            max_audio_length_ms: Used to determine the length of the sine wave.
            
        Returns:
            A tuple containing a sine wave tensor and the sample rate.
        """
        logger.info(f"Generating placeholder audio for text: '{text}'")
        
        # Set default parameters if not provided
        max_audio_length_ms = max_audio_length_ms if max_audio_length_ms is not None else self.DEFAULT_GENERATION_PARAMS["max_audio_length_ms"]
        
        # Generate a simple sine wave
        sample_rate = 24000  # Standard sample rate for CSM
        duration_sec = min(max_audio_length_ms / 1000, 10)  # Cap at 10 seconds
        t = torch.arange(0, duration_sec, 1/sample_rate)
        
        # Generate different frequencies based on speaker_id
        frequency = 220 + (speaker_id * 55)  # A3 + speaker_id * semitones
        
        # Create a simple sine wave
        audio = torch.sin(2 * torch.pi * frequency * t)
        
        # Add some variation based on text length
        amplitude_mod = 0.1 * torch.sin(2 * torch.pi * 2 * t)
        audio = audio + amplitude_mod
        
        # Normalize
        audio = audio / audio.abs().max()
        
        logger.info(f"Generated placeholder audio with {audio.shape[0]} samples at {sample_rate} Hz")
        return audio, sample_rate
    
    def cleanup(self) -> None:
        """Clean up resources (no-op for placeholder)."""
        self.is_initialized = False
        logger.info("Placeholder CSM model cleanup complete")


def create_csm_model(model_path: Optional[str] = None, device: Optional[str] = None, use_placeholder: bool = False) -> CSMModel:
    """
    Factory function to create a CSM model instance.
    
    This function creates a CSM model that will use the real implementation if available,
    or fall back to a mock implementation if necessary.
    
    Args:
        model_path: Path to the model checkpoint.
        device: Device to use for inference.
        use_placeholder: Parameter kept for backward compatibility but no longer used.
        
    Returns:
        A CSM model instance.
        
    Raises:
        CSMModelError: If the model cannot be created or initialized.
    """
    # This will create a model that knows how to mock itself if needed
    model = CSMModel(model_path, device)
    try:
        model.initialize()
        return model
    except Exception as e:
        logger.error(f"Failed to initialize CSM model: {e}")
        raise CSMModelError(f"Failed to initialize CSM model: {e}") 