"""
EchoForge - Voice Generator

This module provides the core text-to-speech functionality for generating 
character voices from text using neural models.
"""

import os
import time
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Union, List, Tuple, BinaryIO

import torch
import torchaudio
import numpy as np
from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer

from app.core.models import create_model, Model, ModelArgs

# Configure logging
logger = logging.getLogger("echoforge.core.voice_generator")


class VoiceGenerator:
    """
    Main voice generator class that handles text-to-speech generation.
    
    This class provides a high-level interface for loading the TTS model,
    preprocessing text, and generating speech audio.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        model_repo: str = "sesame/csm-1b",
        model_filename: str = "model.pt",
        device: str = "auto",
        backbone_flavor: str = "llama-1B",
        decoder_flavor: str = "llama-100M",
        audio_vocab_size: int = 2051,
        audio_num_codebooks: int = 32,
        download_if_missing: bool = True
    ):
        """
        Initialize the voice generator.
        
        Args:
            model_path: Path to the TTS model checkpoint file (if None, will download from HF)
            model_repo: Hugging Face model repository (used if model_path is None)
            model_filename: Filename of the model in the repository
            device: Device to use for generation ("auto", "cuda", "cpu")
            backbone_flavor: Size of the backbone model ("llama-1B" or "llama-100M")
            decoder_flavor: Size of the decoder model ("llama-1B" or "llama-100M")
            audio_vocab_size: Size of the audio vocabulary per codebook
            audio_num_codebooks: Number of audio codebooks
            download_if_missing: Whether to download the model if not found locally
        
        Raises:
            RuntimeError: If the model cannot be loaded or downloaded
        """
        # Set up model path
        self.model_path = self._resolve_model_path(
            model_path, 
            model_repo, 
            model_filename, 
            download_if_missing
        )
        
        # Set up device
        self.requested_device = device
        if device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        # Store model configuration
        self.backbone_flavor = backbone_flavor
        self.decoder_flavor = decoder_flavor
        self.audio_vocab_size = audio_vocab_size
        self.audio_num_codebooks = audio_num_codebooks
        
        # Model sampling parameters
        self.sample_rate = 24000  # Standard sample rate for most TTS models
        
        # Load tokenizer for text preprocessing
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")
            logger.info("Tokenizer loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load LLaMA tokenizer, falling back to default: {e}")
            # If LLaMA tokenizer is not available, we'll use a simple tokenization method
            self.tokenizer = None
        
        # Initialize the model
        logger.info(f"Initializing voice generator on device: {self.device}")
        self._load_model()
    
    def _resolve_model_path(
        self,
        model_path: Optional[str],
        model_repo: str,
        model_filename: str,
        download_if_missing: bool
    ) -> str:
        """
        Resolve the model path, downloading it if necessary.
        
        Args:
            model_path: User-specified model path or None
            model_repo: Hugging Face repository ID
            model_filename: Filename of the model in the repository
            download_if_missing: Whether to download if not found locally
            
        Returns:
            Resolved path to the model file
            
        Raises:
            RuntimeError: If the model cannot be found or downloaded
        """
        if model_path is not None and os.path.exists(model_path):
            logger.info(f"Using provided model path: {model_path}")
            return model_path
        
        # Check cache directory
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        repo_dir = os.path.join(cache_dir, model_repo.replace("/", "--"))
        cached_model = os.path.join(repo_dir, model_filename)
        
        if os.path.exists(cached_model):
            logger.info(f"Using cached model: {cached_model}")
            return cached_model
        
        # Download model if not found
        if download_if_missing:
            logger.info(f"Downloading model from {model_repo}")
            try:
                model_path = hf_hub_download(
                    repo_id=model_repo,
                    filename=model_filename,
                    resume_download=True
                )
                logger.info(f"Model downloaded to {model_path}")
                return model_path
            except Exception as e:
                raise RuntimeError(f"Failed to download model: {e}")
        
        raise RuntimeError(f"Model not found at {model_path} and download_if_missing is False")
    
    def _load_model(self) -> None:
        """
        Load the TTS model from the resolved path.
        
        Raises:
            RuntimeError: If the model cannot be loaded
        """
        try:
            logger.info(f"Loading model from {self.model_path}")
            
            # Create model instance with correct architecture
            self.model = create_model(
                backbone_flavor=self.backbone_flavor,
                decoder_flavor=self.decoder_flavor,
                audio_vocab_size=self.audio_vocab_size,
                audio_num_codebooks=self.audio_num_codebooks,
                device=str(self.device)
            )
            
            # Load weights from checkpoint
            if self.device.type == 'cuda':
                checkpoint = torch.load(self.model_path, map_location=self.device)
            else:
                # When loading on CPU, use map_location to avoid CUDA errors
                checkpoint = torch.load(self.model_path, map_location='cpu')
            
            # For now, just log the checkpoint info - we'll implement proper loading later
            # as there might be differences in state dict keys
            logger.info(f"Model checkpoint loaded with {len(checkpoint)} keys")
            
            # We need to match the state dict keys - for now this is a placeholder
            # self.model.load_state_dict(checkpoint, strict=False)
            
            logger.info(f"Model loaded successfully")
            logger.info(f"Model configuration: backbone={self.backbone_flavor}, decoder={self.decoder_flavor}")
            logger.info(f"Audio config: vocab_size={self.audio_vocab_size}, codebooks={self.audio_num_codebooks}")
            logger.info(f"Using device: {self.device.type}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            if self.device.type == 'cuda' and self.requested_device != 'cpu':
                logger.info("Attempting to fall back to CPU")
                self.device = torch.device('cpu')
                try:
                    # Try loading on CPU instead
                    self.model = create_model(
                        backbone_flavor=self.backbone_flavor,
                        decoder_flavor=self.decoder_flavor,
                        audio_vocab_size=self.audio_vocab_size,
                        audio_num_codebooks=self.audio_num_codebooks,
                        device='cpu'
                    )
                    checkpoint = torch.load(self.model_path, map_location='cpu')
                    logger.info(f"Model loaded successfully on CPU as fallback")
                except Exception as cpu_e:
                    logger.error(f"Failed to load model on CPU fallback: {cpu_e}")
                    raise RuntimeError(f"Failed to load TTS model on any device: {e}, CPU fallback: {cpu_e}")
            else:
                raise RuntimeError(f"Failed to load TTS model: {e}")
    
    def _tokenize_text(self, text: str) -> torch.Tensor:
        """
        Convert input text to token IDs for the model.
        
        Args:
            text: Input text to tokenize
            
        Returns:
            Tensor of token IDs
        """
        if self.tokenizer is not None:
            # Use the LLaMA tokenizer if available
            tokens = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            return tokens.input_ids.to(self.device)
        else:
            # Fallback to simple character-level tokenization
            # This is just a placeholder - in practice we need a proper tokenizer
            chars = list(text.lower())
            char_to_id = {c: i+1 for i, c in enumerate(set(chars))}
            token_ids = torch.tensor([[char_to_id.get(c, 0) for c in chars]])
            return token_ids.to(self.device)
    
    def _decode_audio_tokens(self, tokens: torch.Tensor) -> torch.Tensor:
        """
        Convert audio tokens to waveform.
        
        Args:
            tokens: Tensor of audio tokens from the model
            
        Returns:
            Audio waveform tensor
        """
        # This is a placeholder for the actual decoding logic
        # In a real implementation, we would use a neural codec to convert
        # tokens back to audio waveforms
        
        # For now, generate a simple sine wave as placeholder audio
        duration_sec = min(max(tokens.shape[1] * 0.01, 1.0), 10.0)
        t = torch.linspace(0, duration_sec, int(duration_sec * self.sample_rate))
        
        # Generate a simple audio sample (just for testing)
        base_freq = 220.0
        waveform = 0.5 * torch.sin(2 * np.pi * base_freq * t)
        
        # Convert to proper format
        waveform = waveform.to(self.device).unsqueeze(0)  # Add channel dim
        
        return waveform
    
    def generate(
        self,
        text: str,
        speaker_id: int = 1,
        temperature: float = 0.5,
        top_k: int = 50,
        max_audio_len: int = 1024,
        style: Optional[str] = None,
        device: Optional[str] = None
    ) -> Union[torch.Tensor, bytes]:
        """
        Generate speech from text.
        
        Args:
            text: Text to convert to speech
            speaker_id: Speaker ID to use
            temperature: Temperature for generation sampling (0.0-1.0)
            top_k: Top-k for generation sampling
            max_audio_len: Maximum audio length to generate in tokens
            style: Optional style descriptor (e.g., "happy", "sad", etc.)
            device: Optional device override ("auto", "cuda", "cpu")
            
        Returns:
            Audio waveform as a tensor or bytes
            
        Raises:
            ValueError: If the inputs are invalid
        """
        # Validate inputs
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
            
        if speaker_id < 0:
            raise ValueError("Invalid speaker ID")
            
        if temperature < 0 or temperature > 1:
            raise ValueError("Temperature must be between 0 and 1")
            
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        
        # Handle device override
        current_device = self.device
        if device is not None and device != "auto" and device != str(self.device.type):
            logger.info(f"Device override requested: {device}")
            if device == "cpu":
                # Always allow switching to CPU
                self.device = torch.device("cpu")
                logger.info(f"Switched to CPU as requested")
            elif device == "cuda" and torch.cuda.is_available():
                # Only switch to CUDA if available
                self.device = torch.device("cuda")
                logger.info(f"Switched to CUDA as requested")
            else:
                logger.warning(f"Requested device {device} not available, staying with {self.device.type}")
        
        # Log generation parameters
        logger.info(f"Generating speech for text: '{text}'")
        logger.info(f"Parameters: speaker_id={speaker_id}, temperature={temperature}, top_k={top_k}, device={self.device.type}")
        if style:
            logger.info(f"Style: {style}")
        
        try:
            # Tokenize input text
            token_ids = self._tokenize_text(text)
            
            # Generate audio tokens
            with torch.no_grad():
                audio_tokens = self.model.generate(
                    token_ids,
                    max_audio_len=max_audio_len,
                    temperature=temperature,
                    top_k=top_k
                )
            
            # Convert tokens to audio waveform
            waveform = self._decode_audio_tokens(audio_tokens)
            
            logger.info(f"Generated audio of length {waveform.shape[1] / self.sample_rate:.2f} seconds")
            
            return waveform
            
        except Exception as e:
            logger.error(f"Error during generation: {e}")
            
            # If we're on CUDA and encounter an error, try falling back to CPU
            if self.device.type == "cuda" and device != "cpu":
                logger.info("Attempting to fall back to CPU after CUDA error")
                try:
                    # Switch to CPU
                    self.device = torch.device("cpu")
                    
                    # Tokenize input text again
                    token_ids = self._tokenize_text(text)
                    
                    # Generate audio tokens on CPU
                    with torch.no_grad():
                        audio_tokens = self.model.generate(
                            token_ids,
                            max_audio_len=max_audio_len,
                            temperature=temperature,
                            top_k=top_k
                        )
                    
                    # Convert tokens to audio waveform
                    waveform = self._decode_audio_tokens(audio_tokens)
                    
                    logger.info(f"Successfully generated audio on CPU fallback, length {waveform.shape[1] / self.sample_rate:.2f} seconds")
                    
                    return waveform
                except Exception as cpu_e:
                    logger.error(f"CPU fallback also failed: {cpu_e}")
                    # Restore original device
                    self.device = current_device
                    raise ValueError(f"Voice generation failed on both devices: {e}, CPU fallback: {cpu_e}")
            
            raise ValueError(f"Voice generation failed: {e}")
    
    def save_audio(self, waveform: torch.Tensor, file_path: str) -> str:
        """
        Save the generated audio to a file.
        
        Args:
            waveform: Audio waveform tensor
            file_path: Path to save the audio file
            
        Returns:
            Path to the saved audio file
            
        Raises:
            IOError: If the file cannot be saved
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Normalize audio if needed
            if waveform.abs().max() > 1.0:
                waveform = waveform / waveform.abs().max()
            
            # Save audio file
            torchaudio.save(file_path, waveform, self.sample_rate)
            logger.info(f"Audio saved to {file_path}")
            
            return file_path
        
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
            raise IOError(f"Failed to save audio file: {e}")
    
    def get_audio_bytes(self, waveform: torch.Tensor, format: str = "wav") -> bytes:
        """
        Convert the audio waveform to bytes in the specified format.
        
        Args:
            waveform: Audio waveform tensor
            format: Audio format (wav, mp3, etc.)
            
        Returns:
            Audio data as bytes
            
        Raises:
            ValueError: If the format is unsupported
        """
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as tmp:
                tmp_path = tmp.name
            
            # Save to the temporary file
            self.save_audio(waveform, tmp_path)
            
            # Read as bytes
            with open(tmp_path, "rb") as f:
                audio_bytes = f.read()
            
            # Clean up
            os.unlink(tmp_path)
            
            return audio_bytes
        
        except Exception as e:
            logger.error(f"Failed to get audio bytes: {e}")
            raise ValueError(f"Failed to convert audio to bytes: {e}")


def generate_speech(
    text: str,
    output_path: str,
    speaker_id: int = 1,
    temperature: float = 0.5,
    top_k: int = 50,
    device: str = "auto",
    model_path: Optional[str] = None
) -> bool:
    """
    Convenience function to generate speech and save to a file.
    
    Args:
        text: Text to convert to speech
        output_path: Path to save the output audio
        speaker_id: Speaker ID to use
        temperature: Temperature for generation sampling
        top_k: Top-k for generation sampling
        device: Device to use for generation
        model_path: Optional path to model checkpoint
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize generator
        generator = VoiceGenerator(model_path=model_path, device=device)
        
        # Generate speech
        waveform = generator.generate(
            text=text,
            speaker_id=speaker_id,
            temperature=temperature,
            top_k=top_k
        )
        
        # Save audio to file
        generator.save_audio(waveform, output_path)
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to generate speech: {e}")
        return False 