"""
API routes for the EchoForge application.

This module defines the API endpoints for voice generation and status checking.
"""

import os
import logging
import time
from typing import Dict, Any, List, Optional
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Body, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Import the voice generator
from app.api.voice_generator import voice_generator
from app.core.task_manager import TaskManager

# Setup logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/v1", tags=["api"])

# Task manager for handling background tasks
task_manager = TaskManager()

# Request and response models
class GenerationOptions(BaseModel):
    """Model for generation options."""
    temperature: float = Field(0.5, ge=0.0, le=1.0, description="Controls randomness in generation")
    top_k: int = Field(80, ge=1, le=100, description="Limits token selection to top k most likely")
    device: str = Field("cpu", description="Device to run generation on (cuda/cpu)")
    style: str = Field("short", description="Voice style")

class GenerateRequest(BaseModel):
    """Model for generate request."""
    text: str = Field(..., min_length=1, max_length=1000, description="Text to convert to speech")
    speaker_id: int = Field(1, ge=1, description="ID of the speaker voice to use")
    options: Optional[GenerationOptions] = Field(None, description="Generation options")

class GenerateResponse(BaseModel):
    """Model for generate response."""
    task_id: str = Field(..., description="ID of the generation task")
    status: str = Field("pending", description="Status of the generation task")

class TaskStatusResponse(BaseModel):
    """Model for task status response."""
    task_id: str = Field(..., description="ID of the task")
    status: str = Field(..., description="Status of the task (pending, processing, completed, failed)")
    progress: float = Field(0.0, description="Progress of the task (0-100)")
    result_url: Optional[str] = Field(None, description="URL to the generated voice file")
    error: Optional[str] = Field(None, description="Error message if task failed")

class VoiceInfo(BaseModel):
    """Model for voice information."""
    speaker_id: int = Field(..., description="ID of the speaker voice")
    name: str = Field(..., description="Name of the voice")
    gender: str = Field(..., description="Gender of the voice")
    description: str = Field(..., description="Description of the voice")
    sample_url: Optional[str] = Field(None, description="URL to a sample of the voice")

# API endpoints
@router.get("/voices", response_model=List[VoiceInfo])
async def list_voices():
    """
    List all available voices.
    """
    try:
        voices = voice_generator.list_available_voices()
        return voices
    except Exception as e:
        logger.error(f"Error listing voices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list voices: {str(e)}")

@router.post("/generate", response_model=GenerateResponse)
async def generate_voice(
    request: GenerateRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate voice from text.
    
    The generation is performed asynchronously and a task ID is returned.
    Use the /tasks/{task_id} endpoint to check the status of the task.
    """
    # Validate request
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # Create task ID
    task_id = str(uuid.uuid4())
    
    # Get options with defaults if not provided
    options = request.options or GenerationOptions()
    
    # Create task metadata
    task_data = {
        "text": request.text,
        "speaker_id": request.speaker_id,
        "temperature": options.temperature,
        "top_k": options.top_k,
        "device": options.device,
        "style": options.style,
        "created_at": time.time(),
    }
    
    # Register task
    task_manager.register_task(task_id, task_data)
    
    # Add background task for generation
    background_tasks.add_task(
        _generate_voice_task,
        task_id=task_id,
        text=request.text,
        speaker_id=request.speaker_id,
        temperature=options.temperature,
        top_k=options.top_k,
        device=options.device,
        style=options.style
    )
    
    return {"task_id": task_id, "status": "pending"}

@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the status of a voice generation task.
    """
    # Check if task exists
    task = task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Build response
    response = {
        "task_id": task_id,
        "status": task["status"],
        "progress": task.get("progress", 0.0),
        "result_url": None,
        "error": None
    }
    
    # Add result URL if completed
    if task["status"] == "completed" and "output_path" in task:
        output_path = task["output_path"]
        filename = os.path.basename(output_path)
        response["result_url"] = f"/api/v1/voices/{filename}"
    
    # Add error if failed
    if task["status"] == "failed" and "error" in task:
        response["error"] = task["error"]
    
    return response

@router.get("/voices/{filename}")
async def get_voice_file(filename: str):
    """
    Get a generated voice file.
    """
    output_dir = voice_generator.output_dir
    file_path = os.path.join(output_dir, filename)
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Voice file {filename} not found")
    
    # Return file
    return FileResponse(
        file_path, 
        media_type="audio/wav",
        filename=filename
    )

# Background task function for voice generation
async def _generate_voice_task(
    task_id: str,
    text: str,
    speaker_id: int,
    temperature: float,
    top_k: int,
    device: str,
    style: str
):
    """Background task to generate voice."""
    try:
        # Update task status
        task_manager.update_task(task_id, {"status": "processing", "progress": 10.0})
        
        # Generate voice
        output_path, error = voice_generator.generate(
            text=text,
            speaker_id=speaker_id,
            temperature=temperature,
            top_k=top_k,
            style=style,
            device=device
        )
        
        # Handle result
        if error:
            task_manager.update_task(task_id, {
                "status": "failed",
                "error": error,
                "progress": 100.0
            })
        else:
            task_manager.update_task(task_id, {
                "status": "completed",
                "output_path": output_path,
                "progress": 100.0
            })
            
    except Exception as e:
        logger.error(f"Error in voice generation task: {str(e)}")
        task_manager.update_task(task_id, {
            "status": "failed",
            "error": f"Internal server error: {str(e)}",
            "progress": 100.0
        }) 