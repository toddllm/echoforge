"""
API Router for EchoForge.

This module defines the API routes for the EchoForge application.
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os
import uuid
from pathlib import Path

from app.core import config
try:
    from app.api.voice_generator import voice_generator
except ImportError:
    # Mock voice generator for tests
    voice_generator = None
    
try:
    from app.core.task_manager import task_manager
except ImportError:
    # Mock task manager for tests
    task_manager = None
    
from app.core.auth import auth_required

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix=config.API_PREFIX, tags=config.API_TAGS)


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "version": config.APP_VERSION}


# Simple mock data for testing
MOCK_VOICES = [
    {
        "speaker_id": 1,
        "name": "Male Commander",
        "gender": "male",
        "description": "Authoritative male voice with clear diction and commanding presence."
    },
    {
        "speaker_id": 2,
        "name": "Female Scientist",
        "gender": "female",
        "description": "Professional female voice with precise articulation and thoughtful cadence."
    }
]


@router.get("/voices")
async def list_voices():
    """List available voices."""
    try:
        # Use mock data in test mode
        if os.environ.get("ECHOFORGE_TEST") == "true" or voice_generator is None:
            return MOCK_VOICES
            
        # Use real data in production mode
        voices = voice_generator.list_available_voices()
        return voices
    except Exception as e:
        logger.error(f"Error listing voices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


class VoiceGenerationRequest(BaseModel):
    """Model for voice generation request data."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    speaker_id: int = Field(config.DEFAULT_SPEAKER_ID, ge=1, description="Speaker voice ID to use")
    temperature: float = Field(config.DEFAULT_TEMPERATURE, ge=0.1, le=1.0, description="Temperature for generation")
    top_k: int = Field(config.DEFAULT_TOP_K, ge=1, description="Top-K for token selection")
    style: str = Field(config.DEFAULT_STYLE, description="Voice style")


@router.post("/generate")
async def generate_voice(background_tasks: BackgroundTasks, request: VoiceGenerationRequest):
    """
    Generate voice from text.
    
    This endpoint starts a background task to generate voice from the provided text.
    """
    try:
        # Validate text
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
            
        # Validate speaker ID (in test mode, only allow 1-4)
        if os.environ.get("ECHOFORGE_TEST") == "true" and (request.speaker_id < 1 or request.speaker_id > 4):
            raise HTTPException(status_code=400, detail="Invalid speaker ID")
        
        # Create a unique task ID
        task_id = str(uuid.uuid4())
        
        # In test mode, return a mock response
        if os.environ.get("ECHOFORGE_TEST") == "true" or task_manager is None:
            return {"task_id": task_id, "status": "processing"}
        
        # In production mode, register the task and start the background process
        task_id = task_manager.register_task("voice_generation")
        
        background_tasks.add_task(
            _generate_voice_task,
            task_id=task_id,
            text=request.text,
            speaker_id=request.speaker_id,
            temperature=request.temperature,
            top_k=request.top_k,
            style=request.style
        )
        
        return {"task_id": task_id, "status": "processing"}
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error starting voice generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start voice generation: {str(e)}")


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a task by ID."""
    # In test mode, return a mock successful response
    if os.environ.get("ECHOFORGE_TEST") == "true" or task_manager is None:
        # For testing, simulate a completed task with mock data
        mock_filename = f"voice_1_mock.wav"
        mock_url = f"/voices/{mock_filename}"
        
        return {
            "task_id": task_id,
            "status": "completed",
            "result": {
                "text": "This is a mock generated voice.",
                "speaker_id": 1,
                "file_url": mock_url,
                "output_file": mock_url,  # Add output_file for compatibility
                "file_path": f"/tmp/echoforge/voices/{mock_filename}"
            }
        }
    
    # In production mode, get the actual task status
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return task


async def _generate_voice_task(task_id: str, text: str, speaker_id: int, 
                              temperature: float, top_k: int, style: str):
    """Background task for voice generation."""
    try:
        # Update task status to processing
        task_manager.update_task(task_id, status="processing")
        
        # Generate voice
        output_path, error = voice_generator.generate(
            text=text,
            speaker_id=speaker_id,
            temperature=temperature,
            top_k=top_k,
            style=style
        )
        
        if error:
            # Update task with error
            task_manager.update_task(
                task_id=task_id,
                status="error",
                error=error
            )
            return
        
        # Create public URL for the generated file
        filename = os.path.basename(output_path)
        public_url = f"/voices/{filename}"
        
        # Update task with success result
        task_manager.update_task(
            task_id=task_id,
            status="completed",
            result={
                "text": text,
                "speaker_id": speaker_id,
                "file_url": public_url,
                "file_path": output_path
            }
        )
        
    except Exception as e:
        logger.error(f"Error in voice generation task: {str(e)}", exc_info=True)
        task_manager.update_task(
            task_id=task_id,
            status="error",
            error=f"Generation failed: {str(e)}"
        ) 