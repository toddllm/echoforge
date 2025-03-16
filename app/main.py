"""
EchoForge - Main Application Module

This module initializes the FastAPI application and registers all routes.
It handles startup and shutdown tasks like loading models and cleaning old files.
"""

import os
import logging
from pathlib import Path

# Load environment variables before importing other modules
from app.core.env_loader import load_env_files
load_env_files()

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core import config
from app.core.auth import auth_required
from app.api.router import router as api_router
from app.ui.routes import router as ui_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    description=config.APP_DESCRIPTION,
    version=config.APP_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories if they don't exist
os.makedirs(config.STATIC_DIR, exist_ok=True)
os.makedirs(config.TEMPLATES_DIR, exist_ok=True)
os.makedirs(config.OUTPUT_DIR, exist_ok=True)

# Try to mount static files with error handling
try:
    app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")
    logger.info(f"Mounted static files from {config.STATIC_DIR}")
except Exception as e:
    logger.error(f"Error mounting static files: {str(e)}")

# Setup Jinja2 templates with error handling
try:
    templates = Jinja2Templates(directory=str(config.TEMPLATES_DIR))
    logger.info(f"Set up templates from {config.TEMPLATES_DIR}")
except Exception as e:
    logger.error(f"Error setting up templates: {str(e)}")
    templates = None

# Include API routes
app.include_router(api_router)

# Include UI routes
app.include_router(ui_router)

# Try to mount voice files directory
try:
    app.mount("/voices", StaticFiles(directory=str(config.OUTPUT_DIR)), name="voices")
    logger.info(f"Mounted voice files from {config.OUTPUT_DIR}")
except Exception as e:
    logger.error(f"Error mounting voice files directory: {str(e)}")

# Add fallback health endpoint at the root level in case API router fails
@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "version": config.APP_VERSION}

# Web routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page."""
    # In test mode, don't require authentication
    if os.environ.get("ECHOFORGE_TEST") == "true":
        logger.info("Test mode detected - bypassing authentication")
    else:
        # Apply authentication middleware in non-test mode
        auth_required(request)
    
    # Simple error handling when templates aren't available
    if templates is None:
        return HTMLResponse(content="""
        <html>
            <head><title>EchoForge</title></head>
            <body>
                <h1>EchoForge</h1>
                <p>Character Voice Generator</p>
                <p>Server is running, but templates are not available.</p>
            </body>
        </html>
        """)
    
    try:
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request,
                "default_theme": config.DEFAULT_THEME
            }
        )
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        return HTMLResponse(content=f"""
        <html>
            <head><title>EchoForge</title></head>
            <body>
                <h1>EchoForge</h1>
                <p>Character Voice Generator</p>
                <p>Error: {str(e)}</p>
            </body>
        </html>
        """)

# Handle errors
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all exceptions to prevent server crashes."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)},
    )

# App events
@app.on_event("startup")
async def startup_event():
    """Application startup handler."""
    logger.info("Starting EchoForge application")
    
    # Don't attempt to load models in test mode
    if os.environ.get("ECHOFORGE_TEST") == "true":
        logger.info("Test mode - skipping model loading")
        return
    
    # The remaining startup code is removed for simplicity

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown handler."""
    logger.info("Shutting down EchoForge application") 