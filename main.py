#!/usr/bin/env python3
"""
EchoForge - AI-Powered Character Voice Creation
Main application entry point
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project directory to the path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(BASE_DIR, "echoforge.log")),
    ],
)
logger = logging.getLogger("echoforge")

def create_app():
    """Create and configure the Flask application."""
    from flask import Flask
    from flask_cors import CORS
    
    # Import routes after app initialization to avoid circular imports
    from app.api.routes import register_api_routes
    from app.ui.routes import register_ui_routes
    
    app = Flask(
        __name__,
        static_folder=os.path.join(BASE_DIR, "static"),
        template_folder=os.path.join(BASE_DIR, "templates"),
    )
    
    # Load configuration
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-key-for-development-only"),
        DATA_DIR=os.path.join(BASE_DIR, "data"),
        VOICE_DIR=os.path.join(BASE_DIR, "data", "voices"),
        CHARACTER_DIR=os.path.join(BASE_DIR, "data", "characters"),
        OUTPUT_DIR=os.path.join(BASE_DIR, "data", "output"),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16 MB max upload size
        ALLOWED_EXTENSIONS={"wav", "mp3", "json"},
    )
    
    # Enable CORS
    CORS(app)
    
    # Ensure required directories exist
    for directory in [
        app.config["DATA_DIR"],
        app.config["VOICE_DIR"],
        app.config["CHARACTER_DIR"],
        app.config["OUTPUT_DIR"],
    ]:
        os.makedirs(directory, exist_ok=True)
    
    # Register blueprints
    register_api_routes(app)
    register_ui_routes(app)
    
    return app

def main():
    """Run the application."""
    app = create_app()
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    
    # Run the app
    app.run(
        host="0.0.0.0",
        port=port,
        debug=os.getenv("FLASK_ENV") == "development",
    )
    
    logger.info(f"EchoForge server started on port {port}")

if __name__ == "__main__":
    main()
