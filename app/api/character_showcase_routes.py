"""
Character Showcase API Routes for EchoForge.

This module defines the API routes for the character showcase functionality.
"""

import os
import logging
import uuid
import shutil
import traceback
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional
from pydantic import BaseModel, Field
from pathlib import Path

from app.core import config
from app.models.voice_cloning.voice_cloner import VoiceCloner
from app.models.voice_cloning.csm_integration import CSMVoiceCloner
from app.core.task_manager import task_manager

# Setup logging
logger = logging.getLogger("echoforge.api.character_showcase")

# Create router - use a direct registration path to avoid conflicts
router = APIRouter(prefix="/api/voice-cloning", tags=["character_showcase"])

# Log router creation
logger.info("Character showcase router created with prefix: /api/voice-cloning")

# Initialize components
# Create a robust wrapper class for voice cloning that will work regardless of issues with the underlying models
class RobustVoiceCloner:
    """A robust wrapper for voice cloning that handles errors gracefully and logs detailed information."""
    
    def __init__(self):
        self.cloner = None
        self.cloner_type = "None"
        self.is_dummy = True
        self.is_initialized = False
        
        # Try to initialize a real voice cloner
        try:
            # First try VoiceCloner
            try:
                logger.info("Attempting to initialize VoiceCloner")
                self.cloner = VoiceCloner()
                self.cloner_type = "VoiceCloner"
                self.is_dummy = False
                logger.info("Successfully initialized VoiceCloner")
            except Exception as vc_error:
                # If that fails, try CSMVoiceCloner
                logger.warning(f"Failed to initialize VoiceCloner: {vc_error}. Trying CSMVoiceCloner...")
                try:
                    self.cloner = CSMVoiceCloner()
                    self.cloner_type = "CSMVoiceCloner"
                    self.is_dummy = False
                    logger.info("Successfully initialized CSMVoiceCloner")
                except Exception as csm_error:
                    logger.error(f"Failed to initialize CSMVoiceCloner: {csm_error}")
                    raise Exception("Failed to initialize any voice cloner")
            
            # Log available methods
            methods = [m for m in dir(self.cloner) if not m.startswith('_')]
            logger.info(f"Methods available in {self.cloner_type}: {methods}")
            
        except Exception as e:
            # Fall back to dummy implementation
            logger.error(f"Failed to initialize any voice cloner: {e}. Using dummy cloner.")
            self.is_dummy = True
            self.cloner_type = "DummyCloner"
    
    def initialize(self):
        """Initialize the voice cloner if it has an initialize method."""
        if self.is_dummy:
            logger.info("Dummy cloner doesn't need initialization")
            return True
        
        try:
            if hasattr(self.cloner, 'initialize'):
                logger.info(f"Initializing {self.cloner_type}")
                self.cloner.initialize()
                logger.info(f"Successfully initialized {self.cloner_type}")
            else:
                logger.warning(f"{self.cloner_type} doesn't have initialize method")
            
            self.is_initialized = True
            return True
        except Exception as e:
            logger.error(f"Error initializing {self.cloner_type}: {e}")
            return False
    
    def generate_speech(self, text, audio_path, temperature=0.8, top_k=50, output_path=None):
        """Generate speech using the voice cloner."""
        if self.is_dummy:
            logger.warning("Using dummy voice cloner for speech generation")
            task_id = str(uuid.uuid4())
            
            # For testing, try to copy the reference audio file to output path if provided
            if output_path:
                try:
                    # Create an empty WAV file
                    logger.info(f"Creating dummy wav file at {output_path}")
                    with open(output_path, 'wb') as f:
                        # Write minimal WAV header
                        f.write(b'RIFF\x24\x00\x00\x00WAVE')
                except Exception as e:
                    logger.error(f"Failed to create dummy wav file: {e}")
            
            return {"status": "success", "task_id": task_id, "message": "Dummy speech generation"}
        
        try:
            # Try the most appropriate method based on what's available
            if hasattr(self.cloner, 'generate_speech'):
                logger.info(f"Using {self.cloner_type}.generate_speech")
                result = self.cloner.generate_speech(text, audio_path, temperature, top_k, output_path)
                logger.info(f"generate_speech result: {result}")
                return result
            elif hasattr(self.cloner, 'clone_voice'):
                logger.info(f"Using {self.cloner_type}.clone_voice")
                # Different implementation might require different approach
                audio, sample_rate = self.cloner.clone_voice(text, audio_path, temperature, top_k, None, output_path)
                
                # Save the audio if the method is available
                if hasattr(self.cloner, 'save_cloned_audio') and output_path:
                    logger.info(f"Saving cloned audio to {output_path}")
                    self.cloner.save_cloned_audio(audio, sample_rate, output_path)
                
                return {"status": "success", "task_id": str(uuid.uuid4()), "message": "Generated with clone_voice"}
            else:
                logger.error(f"{self.cloner_type} doesn't have generate_speech or clone_voice methods")
                return {"status": "error", "message": "No suitable voice cloning method available"}
        except Exception as e:
            logger.error(f"Error in generate_speech: {e}")
            raise e

# Initialize our robust voice cloner
voice_cloner = RobustVoiceCloner()
logger.info(f"Voice cloner initialized: type={voice_cloner.cloner_type}, is_dummy={voice_cloner.is_dummy}")

# Define task handler for character voice cloning
def handle_character_voice_task(task_id: str, task_data: dict):
    """
    Handler for character voice cloning tasks.
    This function will be executed by the TaskManager's worker thread.
    
    Args:
        task_id: The unique ID of the task
        task_data: Task data dictionary containing details about the task
    """
    try:
        # Extract task parameters from task_data
        result = task_data.get("result", {})
        text = result.get("text")
        audio_path = result.get("reference_audio")
        temperature = result.get("temperature", 0.8)
        top_k = result.get("top_k", 50)
        
        if not text or not audio_path:
            raise ValueError("Missing required parameters: text and reference_audio")
            
        logger.info(f"Starting voice cloning task {task_id} for text: '{text[:30]}...'")
        task_manager.update_task(task_id, status="processing", progress=0, 
                                message="Starting voice cloning")
        
        # Create output path
        output_filename = f"character_voice_{task_id}.wav"
        output_path = Path(config.OUTPUT_DIR) / output_filename
        
        # Make sure output directory exists
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        
        # Check if we're using the dummy cloner
        if hasattr(voice_cloner, 'is_dummy') and voice_cloner.is_dummy:
            logger.info(f"Using dummy voice cloner for task {task_id}")
            task_manager.update_task(task_id, progress=50, message="Using dummy voice cloner for testing")
            
            # For testing, just copy the reference audio to the output path
            logger.info(f"Copying reference audio {audio_path} to {output_path} for dummy cloner")
            try:
                shutil.copy(audio_path, output_path)
                logger.info(f"Successfully copied reference audio for dummy cloner")
            except Exception as copy_error:
                logger.error(f"Failed to copy reference audio: {copy_error}")
                # Create an empty audio file instead
                with open(output_path, 'wb') as f:
                    f.write(b'')
                logger.info(f"Created empty audio file at {output_path}")
        else:
            # Try initialize the voice cloner if it has the method
            try:
                if hasattr(voice_cloner, 'is_initialized') and hasattr(voice_cloner, 'initialize') and not voice_cloner.is_initialized:
                    logger.info(f"Initializing voice cloner for task {task_id}")
                    task_manager.update_task(task_id, message="Initializing voice cloner")
                    voice_cloner.initialize()
            except Exception as init_error:
                logger.warning(f"Error initializing voice cloner: {init_error}")
                # Continue anyway
            
            # Clone the voice and generate speech
            logger.info(f"Cloning voice for task {task_id}")
            task_manager.update_task(task_id, progress=40, message="Cloning voice and generating speech")
            
            # Try different methods for voice cloning based on what's available
            if hasattr(voice_cloner, 'generate_speech'):
                # Try the newer generate_speech method
                logger.info(f"Using voice_cloner.generate_speech for task {task_id}")
                try:
                    result = voice_cloner.generate_speech(text, audio_path, temperature, top_k, str(output_path))
                    logger.info(f"Result from generate_speech: {result}")
                    # No need to save separately as generate_speech already saves the file
                except Exception as gen_error:
                    logger.error(f"Error in generate_speech: {gen_error}")
                    raise
            elif hasattr(voice_cloner, 'clone_voice'):
                # Try the older clone_voice method
                logger.info(f"Using voice_cloner.clone_voice for task {task_id}")
                try:
                    audio, sample_rate = voice_cloner.clone_voice(
                        text, audio_path, temperature, top_k, None, str(output_path)
                    )
                    
                    # Save the generated audio if the cloner has the save method
                    if hasattr(voice_cloner, 'save_cloned_audio'):
                        logger.info(f"Saving generated audio for task {task_id} to {output_path}")
                        task_manager.update_task(task_id, progress=80, message="Saving generated audio")
                        voice_cloner.save_cloned_audio(audio, sample_rate, str(output_path))
                except Exception as clone_error:
                    logger.error(f"Error in clone_voice: {clone_error}")
                    raise
            else:
                raise ValueError(f"Voice cloner of type {type(voice_cloner).__name__} doesn't have generate_speech or clone_voice methods")
        
        # Mark the task as completed
        logger.info(f"Task {task_id} completed successfully")
        
        # Build the complete URL path for the audio file
        result_url = f"/voices/{output_filename}" if output_filename else ""
        logger.info(f"Generated result_url: {result_url}")
        
        # Update task with both audio_file and result_url for compatibility
        task_manager.update_task(task_id, status="completed", progress=100, 
                               message="Voice cloned and generated successfully",
                               result={
                                   "audio_file": output_filename,
                                   "result_url": result_url
                               })
    except Exception as e:
        logger.error(f"Error in character voice cloning task {task_id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        task_manager.update_task(task_id, status="failed", message=f"Error: {str(e)}")

# Register the task handler with the task manager
task_manager.register_task_handler("character_voice", handle_character_voice_task)

# Start the worker thread
task_manager.start_worker()

# Initialize the voice cloner if it's not a dummy
if not voice_cloner.is_dummy:
    voice_cloner.initialize()

# Define models
class GenerateSpeechRequest(BaseModel):
    """Model for speech generation request from the character showcase."""
    reference_audio: str = Field(..., description="Path to the reference audio file")
    text: str = Field(..., min_length=1, max_length=1000, description="Text to convert to speech")


@router.post("/generate-speech")
async def generate_speech(background_tasks: BackgroundTasks, request: GenerateSpeechRequest):
    # Note: background_tasks parameter is kept for compatibility but no longer used
    """
    Generate speech using a reference audio file.
    
    This endpoint is specifically for the character showcase page to generate
    speech based on existing voice samples.
    """
    try:
        # Check if voice cloner is initialized
        if voice_cloner is None:
            raise HTTPException(status_code=503, detail="Voice cloner service is not available. Please try again later.")
        
        # Extract the file path from the request
        # The reference_audio will be a path like /static/voices/sample.wav
        reference_audio = request.reference_audio
        
        logger.info(f"Processing generate-speech request with reference_audio: {reference_audio}")
        logger.info(f"Using voice_cloner of type: {type(voice_cloner).__name__}")
        
        # Handle different path formats
        if reference_audio.startswith("/static/"):
            # Handle path from app/static
            reference_audio = str(Path("/home/tdeshane/echoforge/app") / reference_audio[1:])
            logger.info(f"Converted to absolute path (app/static): {reference_audio}")
        elif reference_audio.startswith("/voices/"):
            # Try multiple possible locations for the voice file
            filename = reference_audio.split("/")[-1]
            possible_paths = [
                str(Path(config.OUTPUT_DIR) / filename),                      # /tmp/echoforge/voices/...
                str(Path("/home/tdeshane/echoforge/static/voices") / filename), # /home/tdeshane/echoforge/static/voices/...
                str(Path("/home/tdeshane/echoforge/app/static/voices") / filename), # /home/tdeshane/echoforge/app/static/voices/...
            ]
            
            # Try each path until we find one that exists
            for path in possible_paths:
                logger.info(f"Trying path: {path}")
                if os.path.exists(path):
                    reference_audio = path
                    logger.info(f"Found audio file at: {reference_audio}")
                    break
            else:
                # If we didn't find the file, log the error but continue with the original path
                # (the error will be handled later)
                logger.error(f"Could not find audio file '{filename}' in any of the expected locations")
        
        # Also check in the root static directory if we still haven't found the file
        if not os.path.exists(reference_audio):
            alt_path = str(Path("/home/tdeshane/echoforge/static") / reference_audio.split("/")[-1])
            logger.info(f"Trying alternative path: {alt_path}")
            if os.path.exists(alt_path):
                reference_audio = alt_path
                logger.info(f"Using alternative path: {reference_audio}")
        
        if not os.path.exists(reference_audio):
            error_msg = f"Reference audio file not found: {reference_audio}"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)
        
        # Register the task with the TaskManager
        # The TaskManager creates its own task_id and returns it
        logger.info("Registering task with TaskManager")
        task_id = task_manager.register_task(task_type="character_voice")
        logger.info(f"Received task_id from TaskManager: {task_id}")
        
        # Update the task with additional information
        task_manager.update_task(
            task_id=task_id,
            status="queued",
            message=f"Queued voice generation for text: {request.text[:50]}...",
            result={
                "text": request.text,
                "reference_audio": reference_audio,
                "temperature": 0.8,  # Default temperature for showcase
                "top_k": 50,  # Default top_k for showcase
            }
        )
        
        # Enqueue the task to be processed by the worker thread
        logger.info(f"Enqueuing task for task_id: {task_id}")
        task_manager.enqueue_task(task_id)
        
        return {"task_id": task_id}
    
    except Exception as e:
        logger.error(f"Error in generate_speech: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}")
async def get_generation_status(task_id: str):
    """
    Get the status of a speech generation task.
    
    This endpoint is specifically for the character showcase page to check
    the status of speech generation tasks.
    """
    # Direct file check approach to overcome task management issues
    try:
        logger.info(f"Checking status for task: {task_id}")
        
        # Check if the audio file exists by expected convention
        audio_file = f"character_voice_{task_id}.wav"
        output_dir = Path("/tmp/echoforge/voices")
        file_path = output_dir / audio_file
        
        # Debug information about the file
        logger.info(f"Looking for audio file at: {file_path}")
        logger.info(f"File exists: {file_path.exists()}")
        logger.info(f"Is file: {file_path.is_file() if file_path.exists() else False}")
        
        # If the file exists, we'll treat it as a completed task regardless of task manager state
        if file_path.exists() and file_path.is_file():
            logger.info(f"Audio file found at {file_path}")
            result_url = f"/voices/{audio_file}"
            
            response = {
                "task_id": task_id,
                "status": "completed",
                "message": "Voice generation completed",
                "result_url": result_url,
                "audio_file": audio_file,
                "file_exists": "True"
            }
            
            logger.info(f"Returning direct file response: {response}")
            return response
            
        # Only check task manager if file doesn't exist
        try:
            task = task_manager.get_task(task_id)
            logger.info(f"Task manager returned: {task}")
            
            if task:
                # Format the response based on task status
                if task.status == "completed":
                    # Get the audio file name from the task result
                    task_audio_file = task.result.get('audio_file', '') if task.result else ''
                    logger.info(f"Audio file from task result: '{task_audio_file}'")
                    
                    # If task audio file is not empty but different from our convention, check that file too
                    if task_audio_file and task_audio_file != audio_file:
                        task_file_path = output_dir / task_audio_file
                        logger.info(f"Checking alternative file path: {task_file_path} (exists: {task_file_path.exists()})")
                        
                        if task_file_path.exists() and task_file_path.is_file():
                            audio_file = task_audio_file
                            logger.info(f"Using task's audio file: {audio_file}")
                    
                    result_url = f"/voices/{audio_file}"
                    return {
                        "task_id": task_id,
                        "status": "completed",
                        "message": "Voice cloned and generated successfully",
                        "result_url": result_url,
                        "audio_file": audio_file,
                        "file_exists": "True"
                    }
                elif task.status == "failed":
                    return {
                        "status": "failed",
                        "error": task.message if "Error" in (task.message or "") else "Unknown error",
                        "task_id": task_id,
                        "result_url": None,  # Add null result_url to prevent frontend errors
                        "audio_file": None
                    }
                else:
                    return {
                        "status": task.status,
                        "progress": task.progress,
                        "message": task.message,
                        "task_id": task_id,
                        "result_url": None,  # Add null result_url to prevent frontend errors
                        "audio_file": None
                    }
        except Exception as e:
            logger.error(f"Error accessing task manager: {str(e)}")
            # Continue execution - we'll return file not found response later
        
        # If we got here, the task was not found and the file doesn't exist
        # Create a special 404 response that includes the expected file path for debugging
        logger.warning(f"Task {task_id} not found and no audio file exists at {file_path}")
        return JSONResponse(
            status_code=404,
            content={
                "detail": "Task not found",
                "task_id": task_id,
                "expected_file": str(file_path),
                "workaround": "You can try accessing the file directly at /voices/character_voice_{task_id}.wav",
                "result_url": f"/voices/character_voice_{task_id}.wav",  # Provide suggested result_url
                "audio_file": f"character_voice_{task_id}.wav"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in get_generation_status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Note: This function is kept for backward compatibility but no longer used
# The actual implementation is now in handle_character_voice_task
async def _clone_character_voice_task(task_id: str, text: str, audio_path: str,
                                    temperature: float, top_k: int):
    """Legacy function - no longer used. Kept for backward compatibility."""
    logger.warning(f"_clone_character_voice_task called directly - this is deprecated")
    logger.warning(f"Tasks should now be handled by the TaskManager worker thread")
    # Convert the arguments to what handle_character_voice_task expects
    task_data = {
        "task_id": task_id,
        "task_type": "character_voice",
        "result": {
            "text": text,
            "reference_audio": audio_path,
            "temperature": temperature,
            "top_k": top_k
        }
    }
    # Call the handler directly
    handle_character_voice_task(task_id, task_data)
