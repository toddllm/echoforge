"""
EchoForge - Main Application

This is the main entry point for the EchoForge application.
It sets up the FastAPI server and registers all routes.
"""

import os
import logging
import argparse
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.voice_browser import router as voice_browser_router
from app.ui.routes import router as ui_router
from app.core.voice_generator import VoiceGenerator
from app.core import config  # Import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("echoforge")

# Create FastAPI application
app = FastAPI(
    title="EchoForge",
    description="Character Voice Generation Platform",
    version="0.1.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, you'd want to restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "static"),
    name="static"
)

# Include routers
app.include_router(api_router)
app.include_router(ui_router)
app.include_router(voice_browser_router)


@app.on_event("startup")
async def startup_event():
    """Perform startup initialization."""
    logger.info("Starting EchoForge application")
    
    # Create data directories
    data_dir = Path(__file__).parent / "data"
    voices_dir = data_dir / "voices" / "output"
    voices_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Initialized data directories: {data_dir}")
    
    # Initialize voice generator with Direct CSM
    from app.api.voice_generator import voice_generator
    try:
        # Get device from environment or use auto
        device = os.environ.get("ECHOFORGE_DEVICE", "auto")
        logger.info(f"Initializing voice generator with device: {device}")
        
        # Initialize the voice generator
        voice_generator.initialize(device=device)
        
        # Log whether we're using Direct CSM
        if voice_generator.direct_csm is not None:
            logger.info("Voice generator initialized with Direct CSM")
        elif voice_generator.model is not None:
            logger.info("Voice generator initialized with standard CSM model")
        else:
            logger.warning("Voice generator initialized but no model is loaded")
    except Exception as e:
        logger.error(f"Failed to initialize voice generator: {e}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="EchoForge TTS Server")
    parser.add_argument(
        "--host", 
        type=str, 
        default="0.0.0.0", 
        help="Host to bind the server to"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=config.PORT, 
        help="Port to bind the server to"
    )
    parser.add_argument(
        "--model-path", 
        type=str, 
        default=None, 
        help="Path to the TTS model"
    )
    parser.add_argument(
        "--device", 
        type=str, 
        default="auto", 
        help="Device to use for TTS (auto, cuda, cpu)"
    )
    parser.add_argument(
        "--direct-csm", 
        action="store_true", 
        default=True,
        help="Use Direct CSM implementation (default: True)"
    )
    parser.add_argument(
        "--no-direct-csm", 
        action="store_false", 
        dest="direct_csm",
        help="Disable Direct CSM implementation"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode"
    )
    return parser.parse_args()


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    
    # Set environment variables for model settings
    if args.model_path:
        os.environ["ECHOFORGE_MODEL_PATH"] = args.model_path
    os.environ["ECHOFORGE_DEVICE"] = args.device
    
    # Set Direct CSM environment variable
    os.environ["USE_DIRECT_CSM"] = str(args.direct_csm).lower()
    
    # Configure logging level based on debug mode
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Start the server
    logger.info(f"Starting server on {args.host}:{args.port} with Direct CSM {'enabled' if args.direct_csm else 'disabled'}")
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.debug,
        log_level="debug" if args.debug else "info"
    )

