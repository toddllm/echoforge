"""
Voice Cloning module for EchoForge.

This module provides functionality for cloning voices using deep learning models,
leveraging the CSM-1B model for high-quality voice cloning similar to ElevenLabs.
"""

import logging
import os
import sys

# Configure logger
logger = logging.getLogger("echoforge.models.voice_cloning")
logger.info("Initializing voice cloning module")
logger.info(f"Python path: {sys.path}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Module file: {__file__}")

try:
    logger.info("Importing voice_encoder.py module")
    from app.models.voice_cloning.voice_encoder import VoiceEncoder
    logger.info("VoiceEncoder imported successfully")
    
    logger.info("Importing voice_cloner.py module")
    from app.models.voice_cloning.voice_cloner import VoiceCloner
    logger.info("VoiceCloner imported successfully")
    logger.info(f"VoiceCloner attributes: {[attr for attr in dir(VoiceCloner) if not attr.startswith('_')]}")
    
    logger.info("Importing csm_integration.py module")
    from app.models.voice_cloning.csm_integration import CSMVoiceCloner
    logger.info("CSMVoiceCloner imported successfully")
    logger.info(f"CSMVoiceCloner attributes: {[attr for attr in dir(CSMVoiceCloner) if not attr.startswith('_')]}")
    
    # Mark as successfully imported
    VOICE_CLONING_IMPORTED = True
    logger.info("All voice cloning modules imported successfully")
except ImportError as e:
    logger.error(f"Import error in voice cloning module: {e}")
    logger.exception("Import exception details:")
    VOICE_CLONING_IMPORTED = False
except Exception as e:
    logger.error(f"Unexpected error in voice cloning module: {e}")
    logger.exception("Exception details:")
    VOICE_CLONING_IMPORTED = False

# Only export these if successfully imported
if VOICE_CLONING_IMPORTED:
    __all__ = ['VoiceEncoder', 'VoiceCloner', 'CSMVoiceCloner']
else:
    __all__ = []
    logger.warning("Voice cloning modules not exported due to import errors")
