"""
EchoForge - Checkpoint Loader

This module handles loading and converting checkpoints from various sources.
It provides utilities to download, verify, and load model checkpoints.
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple

import torch
from huggingface_hub import hf_hub_download, snapshot_download, scan_cache_dir
from tqdm import tqdm

from app.core.models import Model, ModelArgs

# Configure logging
logger = logging.getLogger("echoforge.core.checkpoint_loader")


class CheckpointLoader:
    """
    Handles loading and verifying model checkpoints.
    
    This class provides utilities to download checkpoints from Hugging Face,
    verify their integrity, and load them into model instances.
    """
    
    DEFAULT_REPO = "sesame/csm-1b"
    DEFAULT_FILENAME = "model.pt"
    
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        progress_bar: bool = True
    ):
        """
        Initialize the checkpoint loader.
        
        Args:
            cache_dir: Directory to store downloaded models (defaults to HF cache)
            progress_bar: Whether to show a progress bar during downloads
        """
        self.cache_dir = cache_dir
        self.progress_bar = progress_bar
        
        # Check for existing cached models
        self._scan_cache()
    
    def _scan_cache(self) -> None:
        """Scan cache directory for existing models."""
        try:
            cache_info = scan_cache_dir()
            model_repos = [
                repo for repo in cache_info.repos 
                if "csm" in repo.repo_id.lower() or "tts" in repo.repo_id.lower()
            ]
            
            if model_repos:
                logger.info(f"Found {len(model_repos)} relevant model repositories in cache:")
                for repo in model_repos:
                    logger.info(f"  - {repo.repo_id} ({len(repo.revisions)} revisions)")
        except Exception as e:
            logger.warning(f"Failed to scan cache directory: {e}")
    
    def download_checkpoint(
        self,
        repo_id: str = DEFAULT_REPO,
        filename: str = DEFAULT_FILENAME,
        revision: Optional[str] = None,
        force_download: bool = False
    ) -> str:
        """
        Download a model checkpoint from Hugging Face Hub.
        
        Args:
            repo_id: Hugging Face repository ID
            filename: Filename of the checkpoint within the repository
            revision: Specific revision to download (tag, branch, or commit)
            force_download: Whether to force re-download even if file exists
            
        Returns:
            Local path to the downloaded checkpoint
            
        Raises:
            RuntimeError: If download fails
        """
        logger.info(f"Downloading checkpoint from {repo_id}, file: {filename}")
        
        try:
            local_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                revision=revision,
                cache_dir=self.cache_dir,
                force_download=force_download,
                resume_download=not force_download
            )
            
            logger.info(f"Checkpoint downloaded to {local_path}")
            
            # Verify file integrity
            self._verify_checkpoint(local_path)
            
            return local_path
            
        except Exception as e:
            logger.error(f"Failed to download checkpoint: {e}")
            raise RuntimeError(f"Failed to download checkpoint: {e}")
    
    def download_repository(
        self,
        repo_id: str = DEFAULT_REPO,
        revision: Optional[str] = None,
        force_download: bool = False
    ) -> str:
        """
        Download an entire repository from Hugging Face Hub.
        
        Args:
            repo_id: Hugging Face repository ID
            revision: Specific revision to download (tag, branch, or commit)
            force_download: Whether to force re-download even if files exist
            
        Returns:
            Local path to the downloaded repository
            
        Raises:
            RuntimeError: If download fails
        """
        logger.info(f"Downloading entire repository: {repo_id}")
        
        try:
            local_path = snapshot_download(
                repo_id=repo_id,
                revision=revision,
                cache_dir=self.cache_dir,
                force_download=force_download,
                resume_download=not force_download
            )
            
            logger.info(f"Repository downloaded to {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"Failed to download repository: {e}")
            raise RuntimeError(f"Failed to download repository: {e}")
    
    def _verify_checkpoint(self, checkpoint_path: str) -> bool:
        """
        Verify the integrity of a checkpoint file.
        
        Args:
            checkpoint_path: Path to the checkpoint file
            
        Returns:
            True if verification passes, False otherwise
        """
        logger.info(f"Verifying checkpoint: {checkpoint_path}")
        
        try:
            # Check file exists and has a reasonable size
            if not os.path.exists(checkpoint_path):
                logger.error(f"Checkpoint file not found: {checkpoint_path}")
                return False
            
            file_size_mb = os.path.getsize(checkpoint_path) / (1024 * 1024)
            if file_size_mb < 10:  # Arbitrary minimum size
                logger.warning(f"Checkpoint file is suspiciously small: {file_size_mb:.2f} MB")
            
            logger.info(f"Checkpoint file size: {file_size_mb:.2f} MB")
            
            # Try to load the file as a PyTorch checkpoint
            checkpoint = torch.load(checkpoint_path, map_location='cpu')
            
            if not isinstance(checkpoint, dict):
                logger.warning(f"Checkpoint is not a dictionary: {type(checkpoint)}")
                return False
            
            # Log some information about the checkpoint
            num_tensors = sum(1 for v in checkpoint.values() if isinstance(v, torch.Tensor))
            logger.info(f"Checkpoint contains {len(checkpoint)} keys ({num_tensors} tensors)")
            
            # Further verification could include hash checking if we had reference hashes
            
            return True
            
        except Exception as e:
            logger.error(f"Checkpoint verification failed: {e}")
            return False
    
    def _convert_checkpoint(
        self, 
        checkpoint: Dict[str, Any],
        model_args: ModelArgs
    ) -> Dict[str, torch.Tensor]:
        """
        Convert a checkpoint to match our model architecture.
        
        Args:
            checkpoint: Raw checkpoint state dict
            model_args: Model architecture configuration
            
        Returns:
            Converted state dict compatible with our model
        """
        logger.info("Converting checkpoint format to match model")
        
        new_state_dict = {}
        mapping_rules = self._get_mapping_rules(model_args)
        
        # Apply mapping rules
        for old_key, new_key in mapping_rules.items():
            if old_key in checkpoint:
                new_state_dict[new_key] = checkpoint[old_key]
            else:
                logger.warning(f"Key not found in checkpoint: {old_key}")
        
        # Count converted items
        logger.info(f"Converted {len(new_state_dict)}/{len(checkpoint)} keys")
        
        return new_state_dict
    
    def _get_mapping_rules(self, model_args: ModelArgs) -> Dict[str, str]:
        """
        Get rules for mapping from checkpoint keys to model keys.
        
        Args:
            model_args: Model architecture configuration
            
        Returns:
            Dictionary mapping from checkpoint keys to model keys
        """
        # This function would need to be adapted based on the actual checkpoint structure
        # For now, we'll define a simple placeholder mapping
        return {
            "backbone.layers.0.attention.q_proj.weight": "backbone_layers.0.attention.q_proj.weight",
            # ... more mapping rules would be defined here
        }
    
    def load_checkpoint(
        self,
        model: Model,
        checkpoint_path: str,
        strict: bool = False
    ) -> bool:
        """
        Load a checkpoint into a model.
        
        Args:
            model: Model instance to load the checkpoint into
            checkpoint_path: Path to the checkpoint file
            strict: Whether to require an exact match between model and checkpoint keys
            
        Returns:
            True if loading succeeds, False otherwise
        """
        logger.info(f"Loading checkpoint from {checkpoint_path} into model")
        
        try:
            # Load the checkpoint file
            checkpoint = torch.load(checkpoint_path, map_location='cpu')
            
            if not isinstance(checkpoint, dict):
                logger.error(f"Checkpoint is not a dictionary: {type(checkpoint)}")
                return False
            
            # Measure state dict compatibility
            model_state = model.state_dict()
            
            # Check for key intersection
            checkpoint_keys = set(checkpoint.keys())
            model_keys = set(model_state.keys())
            
            shared_keys = checkpoint_keys.intersection(model_keys)
            missing_keys = model_keys - checkpoint_keys
            unexpected_keys = checkpoint_keys - model_keys
            
            logger.info(f"Keys in checkpoint: {len(checkpoint_keys)}")
            logger.info(f"Keys in model: {len(model_keys)}")
            logger.info(f"Shared keys: {len(shared_keys)}")
            logger.info(f"Missing keys: {len(missing_keys)}")
            logger.info(f"Unexpected keys: {len(unexpected_keys)}")
            
            # Check if keys need conversion
            if len(shared_keys) < len(model_keys) * 0.5:
                logger.info("Less than 50% of keys match directly, attempting conversion")
                converted_state_dict = self._convert_checkpoint(checkpoint, model.args)
                
                # Try loading the converted state dict
                missing, unexpected = model.load_state_dict(converted_state_dict, strict=False)
                
                if len(missing) > 0:
                    logger.warning(f"Missing keys after conversion: {len(missing)}")
                    if strict:
                        raise RuntimeError(f"Missing keys in checkpoint: {missing}")
                
                if len(unexpected) > 0:
                    logger.warning(f"Unexpected keys after conversion: {len(unexpected)}")
            else:
                # Try loading the state dict directly
                missing, unexpected = model.load_state_dict(checkpoint, strict=False)
                
                if len(missing) > 0:
                    logger.warning(f"Missing keys: {len(missing)}")
                    if strict:
                        raise RuntimeError(f"Missing keys in checkpoint: {missing}")
                
                if len(unexpected) > 0:
                    logger.warning(f"Unexpected keys: {len(unexpected)}")
            
            logger.info(f"Checkpoint loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return False


def load_model_from_checkpoint(
    checkpoint_path: Optional[str] = None,
    model_args: Optional[ModelArgs] = None,
    device: str = "cuda",
    download_if_missing: bool = True
) -> Tuple[Model, str]:
    """
    Load a model from a checkpoint.
    
    Args:
        checkpoint_path: Path to checkpoint file (if None, will download default)
        model_args: Model architecture configuration
        device: Device to load the model onto
        download_if_missing: Whether to download the checkpoint if not found
        
    Returns:
        Tuple of (loaded model, checkpoint path)
    """
    loader = CheckpointLoader()
    
    # Resolve checkpoint path
    if checkpoint_path is None or not os.path.exists(checkpoint_path):
        if download_if_missing:
            checkpoint_path = loader.download_checkpoint()
        else:
            raise ValueError("Checkpoint not found and download_if_missing is False")
    
    # Create model with default args if none provided
    if model_args is None:
        model_args = ModelArgs(device=device)
    
    # Create model instance
    model = Model(model_args).to(device)
    
    # Load checkpoint
    success = loader.load_checkpoint(model, checkpoint_path)
    if not success:
        logger.warning("Loading checkpoint had some issues, model may not behave as expected")
    
    return model, checkpoint_path 