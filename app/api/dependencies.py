"""
EchoForge API Dependencies

This module provides dependencies for the FastAPI routes.
"""

import os
import logging
from functools import lru_cache
from typing import Optional

from fastapi import Depends

from app.core.voice_generator import VoiceGenerator
from app.core.checkpoint_loader import load_model_from_checkpoint

# Configure logging
logger = logging.getLogger("echoforge.api.dependencies")


@lru_cache(maxsize=1)
def get_voice_generator_settings():
    """
    Get settings for the voice generator from environment variables.
    
    Returns:
        Dictionary of voice generator settings
    """
    return {
        "model_path": os.environ.get("ECHOFORGE_MODEL_PATH"),
        "model_repo": os.environ.get("ECHOFORGE_MODEL_REPO", "sesame/csm-1b"),
        "backbone_flavor": os.environ.get("ECHOFORGE_BACKBONE_FLAVOR", "llama-1B"),
        "decoder_flavor": os.environ.get("ECHOFORGE_DECODER_FLAVOR", "llama-100M"),
        "device": os.environ.get("ECHOFORGE_DEVICE", "auto"),
    }


@lru_cache(maxsize=1)
def get_voice_generator():
    """
    Get a singleton voice generator instance.
    
    Returns:
        Voice generator instance with the model loaded
    """
    logger.info("Initializing voice generator")
    
    # Get settings
    settings = get_voice_generator_settings()
    
    # Create voice generator
    generator = VoiceGenerator(
        model_path=settings["model_path"],
        model_repo=settings["model_repo"],
        backbone_flavor=settings["backbone_flavor"],
        decoder_flavor=settings["decoder_flavor"],
        device=settings["device"],
        download_if_missing=True
    )
    
    logger.info("Voice generator initialized")
    return generator 