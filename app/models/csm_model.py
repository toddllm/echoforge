"""
CSM Model Implementation

This module provides a wrapper for the Conversational Speech Model (CSM) from Sesame AI Labs.
It handles model loading, GPU/CPU detection, and provides fallback mechanisms.
"""

import os
import sys
import logging
import torch
import torchaudio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from huggingface_hub import hf_hub_download, snapshot_download

# Configure logging
logger = logging.getLogger(__name__)

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
        Ensure that all required dependencies are available.
        
        Returns:
            True if all dependencies are available, False otherwise.
        """
        try:
            # Check for required modules
            import torch
            import torchaudio
            import transformers
            import huggingface_hub
            import torchtune
            
            # Try to import CSM-specific modules
            try:
                # First try to import from the local csm-1b directory
                sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "csm-1b"))
                from models import Model, ModelArgs
                from generator import Generator, load_llama3_tokenizer
                logger.info("Successfully imported CSM modules from local directory")
                return True
            except ImportError:
                logger.warning("Could not import CSM modules from local directory, will download from Hugging Face")
                return False
                
        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            return False
    
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
            # Ensure dependencies are available
            if not self._ensure_dependencies():
                raise CSMModelLoadError("Missing required dependencies")
            
            # Get the model path
            if self.model_path is None or not os.path.exists(self.model_path):
                self.model_path = self._download_model()
            
            # Import required modules
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "csm-1b"))
            from models import Model, ModelArgs
            from generator import Generator, load_csm_1b
            
            # Load the model
            logger.info(f"Loading CSM model from {self.model_path} on {self.device}")
            
            # Try to use the load_csm_1b function first
            try:
                self.generator = load_csm_1b(self.model_path, self.device)
                logger.info("Successfully loaded CSM model using load_csm_1b")
            except Exception as e:
                logger.warning(f"Could not load model using load_csm_1b: {e}, trying manual loading")
                
                # Manual loading
                model_args = ModelArgs(**self.DEFAULT_MODEL_ARGS)
                self.model = Model(model_args).to(device=self.device, dtype=torch.bfloat16)
                
                # Load checkpoint
                checkpoint = torch.load(self.model_path, map_location=self.device)
                self.model.load_state_dict(checkpoint["model"])
                
                # Create generator
                self.generator = Generator(self.model)
                logger.info("Successfully loaded CSM model manually")
            
            self.is_initialized = True
            logger.info("CSM model initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing CSM model: {e}")
            self.is_initialized = False
            raise CSMModelLoadError(f"Could not initialize CSM model: {e}")
    
    def generate_speech(
        self,
        text: str,
        speaker_id: int = 1,
        temperature: float = None,
        top_k: int = None,
        max_audio_length_ms: float = None,
    ) -> Tuple[torch.Tensor, int]:
        """
        Generate speech from text.
        
        Args:
            text: The text to convert to speech.
            speaker_id: The speaker ID to use.
            temperature: Temperature for sampling. Higher values produce more diverse outputs.
            top_k: Number of highest probability tokens to consider for sampling.
            max_audio_length_ms: Maximum audio length in milliseconds.
            
        Returns:
            A tuple containing the generated audio tensor and the sample rate.
            
        Raises:
            CSMModelError: If the model is not initialized or generation fails.
        """
        if not self.is_initialized:
            try:
                self.initialize()
            except Exception as e:
                raise CSMModelError(f"Model not initialized and initialization failed: {e}")
        
        # Set default parameters if not provided
        temperature = temperature if temperature is not None else self.DEFAULT_GENERATION_PARAMS["temperature"]
        top_k = top_k if top_k is not None else self.DEFAULT_GENERATION_PARAMS["top_k"]
        max_audio_length_ms = max_audio_length_ms if max_audio_length_ms is not None else self.DEFAULT_GENERATION_PARAMS["max_audio_length_ms"]
        
        try:
            logger.info(f"Generating speech for text: '{text}' with speaker_id={speaker_id}, temperature={temperature}, top_k={top_k}")
            
            # Generate speech
            audio = self.generator.generate(
                text=text,
                speaker=speaker_id,
                context=[],  # No context for now
                temperature=temperature,
                topk=top_k,
                max_audio_length_ms=max_audio_length_ms,
            )
            
            sample_rate = self.generator.sample_rate
            logger.info(f"Generated audio with {audio.shape[0]} samples at {sample_rate} Hz")
            
            return audio, sample_rate
            
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            
            # Try to reinitialize the model and try again
            try:
                logger.warning("Attempting to reinitialize model and retry generation")
                self.is_initialized = False
                self.initialize()
                
                audio = self.generator.generate(
                    text=text,
                    speaker=speaker_id,
                    context=[],
                    temperature=temperature,
                    topk=top_k,
                    max_audio_length_ms=max_audio_length_ms,
                )
                
                sample_rate = self.generator.sample_rate
                logger.info(f"Generated audio with {audio.shape[0]} samples at {sample_rate} Hz after reinitialization")
                
                return audio, sample_rate
                
            except Exception as retry_error:
                logger.error(f"Error generating speech after reinitialization: {retry_error}")
                raise CSMModelError(f"Could not generate speech: {e}, retry failed: {retry_error}")
    
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
            
            # Save audio
            torchaudio.save(output_path, audio.unsqueeze(0), sample_rate)
            logger.info(f"Saved audio to {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving audio: {e}")
            raise CSMModelError(f"Could not save audio: {e}")
    
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
    
    This function attempts to create a real CSM model, but falls back to a placeholder
    if the real model cannot be loaded or if use_placeholder is True.
    
    Args:
        model_path: Path to the model checkpoint.
        device: Device to use for inference.
        use_placeholder: Whether to use the placeholder model regardless of real model availability.
        
    Returns:
        A CSM model instance (either real or placeholder).
    """
    if use_placeholder:
        logger.info("Using placeholder CSM model as requested")
        return PlaceholderCSMModel(model_path, device)
    
    try:
        # Try to create and initialize the real model
        model = CSMModel(model_path, device)
        model.initialize()
        return model
    except Exception as e:
        logger.warning(f"Could not create real CSM model: {e}, falling back to placeholder")
        return PlaceholderCSMModel(model_path, device) 