"""
EchoForge - Main Application Module

This module initializes the FastAPI application and registers all routes.
It handles startup and shutdown tasks like loading models and cleaning old files.
"""

import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager

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
from app.api.admin import router as admin_router
from app.core.task_manager import task_manager

# Setup logging
import datetime
import sys

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(logs_dir, exist_ok=True)

# Create a timestamped log filename
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(logs_dir, f"server_{timestamp}.log")

# Create file handler with immediate flushing
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Get app logger
logger = logging.getLogger("echoforge")
logger.info(f"Logging to {log_file}")

# Test log message to verify logging works
logger.info("EchoForge server starting")
logger.info(f"Python version: {sys.version}")
logger.info(f"Log directory: {logs_dir}")

# Define lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting EchoForge application")
    
    # Don't attempt to load models in test mode
    if os.environ.get("ECHOFORGE_TEST") == "true":
        logger.info("Test mode detected - skipping model loading")
    else:
        # In production mode, try to load models
        try:
            # Import here to avoid circular imports
            from app.api.voice_generator import voice_generator
            
            # Initialize voice generator
            if voice_generator:
                logger.info("Initializing voice generator")
                voice_generator.initialize()
        except Exception as e:
            logger.error(f"Error initializing voice generator: {str(e)}")
    
    # Yield control back to FastAPI
    yield
    
    # Shutdown
    logger.info("Shutting down EchoForge application")
    
    # Stop the task manager worker thread
    if task_manager:
        logger.info("Stopping task manager worker thread")
        task_manager.stop_worker()
    
    # Clean up voice cloner resources
    try:
        from app.models.voice_cloning.voice_cloner import get_voice_cloner
        voice_cloner = get_voice_cloner()
        if voice_cloner and hasattr(voice_cloner, 'cleanup'):
            logger.info("Cleaning up voice cloner resources")
            voice_cloner.cleanup()
    except Exception as e:
        logger.error(f"Error cleaning up voice cloner: {str(e)}")
    
    # Clean up CUDA cache
    try:
        import torch
        if torch.cuda.is_available():
            logger.info("Clearing CUDA cache")
            torch.cuda.empty_cache()
    except Exception as e:
        logger.error(f"Error clearing CUDA cache: {str(e)}")
    
    # Clean up old files
    try:
        # Import here to avoid circular imports
        from app.core.task_manager import task_manager
        
        if task_manager:
            logger.info("Cleaning up old tasks")
            task_manager.cleanup_old_tasks()
    except Exception as e:
        logger.error(f"Error during shutdown cleanup: {str(e)}")

# Create the FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    description=config.APP_DESCRIPTION,
    version=config.APP_VERSION,
    lifespan=lifespan,
    openapi_url="/api/v1/openapi.json"
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

# Include Admin API routes
app.include_router(admin_router)

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

# Direct voice-cloning endpoints to bypass router issues
@app.post("/api/voice-cloning/generate-speech")
async def direct_generate_speech(request: Request):
    """Direct endpoint for voice cloning speech generation."""
    logger.info("Direct voice-cloning/generate-speech endpoint called")
    
    try:
        # Import here to avoid circular imports
        try:
            from app.api.character_showcase_routes import generate_speech, GenerateSpeechRequest
            logger.info("Successfully imported generate_speech and GenerateSpeechRequest")
        except ImportError as import_error:
            logger.error(f"Failed to import from character_showcase_routes: {import_error}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Server configuration error", "message": str(import_error)},
            )
            
        from fastapi import BackgroundTasks
        
        # Parse the request body
        try:
            body = await request.json()
            logger.info(f"Request body: {body}")
        except Exception as json_error:
            logger.error(f"Failed to parse request JSON: {json_error}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid JSON in request", "message": str(json_error)},
            )
            
        # Validate required fields
        if not body.get('reference_audio') or not body.get('text'):
            missing_fields = []
            if not body.get('reference_audio'):
                missing_fields.append('reference_audio')
            if not body.get('text'):
                missing_fields.append('text')
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            logger.error(error_msg)
            return JSONResponse(
                status_code=400,
                content={"detail": "Missing required fields", "message": error_msg},
            )
        
        # Build the request model
        try:
            speech_request = GenerateSpeechRequest(**body)
            logger.info(f"Created speech request model: {speech_request}")
        except Exception as model_error:
            logger.error(f"Failed to create GenerateSpeechRequest: {model_error}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid request structure", "message": str(model_error)},
            )
        
        # Create a BackgroundTasks instance
        background_tasks = BackgroundTasks()
        logger.info("Created BackgroundTasks instance")
        
        # Call the actual implementation
        try:
            logger.info("Calling generate_speech function")
            result = await generate_speech(background_tasks, speech_request)
            logger.info(f"generate_speech returned: {result}")
            return result
        except Exception as gen_error:
            logger.error(f"Error in generate_speech function: {gen_error}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Speech generation failed", "message": str(gen_error)},
            )
    except Exception as e:
        logger.error(f"Unexpected error in direct voice-cloning endpoint: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "message": str(e)},
        )


@app.get("/api/voice-cloning/status/{task_id}")
async def get_voice_cloning_status(task_id: str):
    """
    Get the status of a voice cloning task by its ID.
    
    Args:
        task_id: The unique ID of the task to check
        
    Returns:
        The status and details of the voice cloning task
    """
    try:
        logger.info(f"Checking status for voice cloning task: {task_id}")
        
        # Get the task status from the task manager
        task_data = task_manager.get_task(task_id)
        
        if not task_data:
            logger.warning(f"Task not found: {task_id}")
            return JSONResponse(
                status_code=404, 
                content={"detail": "Task not found", "task_id": task_id}
            )
        
        # Extract the status info
        status = task_data.get("status", "unknown")
        result = task_data.get("result", {})
        error = task_data.get("error")
        message = task_data.get("message", "")
        
        response = {
            "task_id": task_id,
            "status": status,
            "message": message
        }
        
        # Include audio_file in response if available
        if result and "audio_file" in result:
            response["audio_file"] = result["audio_file"]
            logger.info(f"Voice cloning task {task_id} completed with file: {result['audio_file']}")
        
        # Include error if present
        if error:
            response["error"] = error
            logger.error(f"Voice cloning task {task_id} failed with error: {error}")
            
        logger.info(f"Returning status for task {task_id}: {status}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting voice cloning status: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Failed to retrieve task status", "message": str(e)}
        )

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

# Write the port to a file for other scripts to use
def write_port_to_file():
    """Write the server port to a file for other scripts to use."""
    port_file = os.path.expanduser("~/.echoforge_port")
    try:
        # Get the port from the runner script's environment variable or use default
        port = os.environ.get("ECHOFORGE_PORT", "8765")
        with open(port_file, "w") as f:
            f.write(port)
        logger.info(f"Server port {port} written to {port_file}")
    except Exception as e:
        logger.error(f"Failed to write port to file: {e}")

# Call this function when the server starts
@app.on_event("startup")
async def startup_event():
    # Get the port from the environment or use default
    port = os.environ.get("ECHOFORGE_PORT", "8765")
    logger.info(f"Starting EchoForge server on port {port}")
    write_port_to_file() 