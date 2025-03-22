"""
Configuration settings for the EchoForge application.

This module contains settings and constants used across the application.
"""

import os
from pathlib import Path

# Import environment loader (must be first)
from app.core import env_loader

# Project directories
ROOT_DIR = Path(__file__).parent.parent.parent.absolute()
STATIC_DIR = ROOT_DIR / "static"
TEMPLATES_DIR = ROOT_DIR / "templates"

# Server settings
DEFAULT_HOST = "127.0.0.1"  # Default to localhost for security
PUBLIC_HOST = os.environ.get("PUBLIC_HOST", "0.0.0.0")  # Host for public serving
ALLOW_PUBLIC_SERVING = os.environ.get("ALLOW_PUBLIC_SERVING", "false").lower() == "true"
# Use 8765 as our unique port for EchoForge
# "8765" can be remembered as it's a sequential number sequence
DEFAULT_PORT = int(os.environ.get("PORT", "8765"))
MAX_PORT_ATTEMPTS = 100

# UI settings
DEFAULT_THEME = os.environ.get("DEFAULT_THEME", "light")  # Options: "light" or "dark"

# Security settings
ENABLE_AUTH = os.environ.get("ENABLE_AUTH", "false").lower() == "true"
# Default username and password - should be changed in production!
AUTH_USERNAME = os.environ.get("AUTH_USERNAME", "echoforge")
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD", "changeme123")
# If public serving is enabled, force authentication by default
AUTH_REQUIRED_FOR_PUBLIC = os.environ.get("AUTH_REQUIRED_FOR_PUBLIC", "true").lower() == "true"

# Model settings
MODEL_PATH = "/home/tdeshane/.cache/huggingface/hub/models--sesame--csm-1b/snapshots/03ab46ff5cfdcc783cc76fcf9ea6fd0838503093/ckpt.pt"
VOICE_CLONER_MODEL_PATH = MODEL_PATH  # Use the same model path for voice cloning
VOICE_ENCODER_MODEL_PATH = MODEL_PATH  # Use the same model path for voice encoding
VOICE_FINE_TUNER_MODEL_PATH = MODEL_PATH  # Use the same model path for voice fine tuning

# Direct CSM settings
USE_DIRECT_CSM = os.environ.get("USE_DIRECT_CSM", "true").lower() == "true"  # Enable by default
DIRECT_CSM_PATH = os.environ.get("DIRECT_CSM_PATH", "/home/tdeshane/tts_poc/voice_poc/csm")
DIRECT_CSM_FALLBACK_TO_STANDARD = os.environ.get("DIRECT_CSM_FALLBACK_TO_STANDARD", "true").lower() == "true"

# Output settings
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/tmp/echoforge/voices")

# Voice generation settings
DEFAULT_TEMPERATURE = float(os.environ.get("DEFAULT_TEMPERATURE", "0.7"))
DEFAULT_TOP_K = int(os.environ.get("DEFAULT_TOP_K", "50"))
DEFAULT_SPEAKER_ID = int(os.environ.get("DEFAULT_SPEAKER_ID", "1"))
DEFAULT_STYLE = os.environ.get("DEFAULT_STYLE", "default")
DEFAULT_DEVICE = os.environ.get("DEFAULT_DEVICE", "auto")

# Task management
MAX_TASKS = int(os.environ.get("MAX_TASKS", "10"))
TASK_CLEANUP_KEEP_NEWEST = int(os.environ.get("TASK_CLEANUP_KEEP_NEWEST", "500"))
VOICE_FILE_MAX_AGE_HOURS = int(os.environ.get("VOICE_FILE_MAX_AGE_HOURS", "24"))

# API settings
API_PREFIX = "/api"
API_TAGS = ["voice"]

# Application info
APP_NAME = "EchoForge"
APP_DESCRIPTION = "Voice generation and management for creative projects"
APP_VERSION = "0.1.0"

# Server settings
HOST = os.environ.get("ECHOFORGE_HOST", "0.0.0.0")
PORT = int(os.environ.get("ECHOFORGE_PORT", 8765))
RELOAD = os.environ.get("ECHOFORGE_RELOAD", "false").lower() == "true"
DEBUG = os.environ.get("ECHOFORGE_DEBUG", "false").lower() == "true"

# Task manager settings
TASK_TIMEOUT = int(os.environ.get("ECHOFORGE_TASK_TIMEOUT", 3600))  # 1 hour 