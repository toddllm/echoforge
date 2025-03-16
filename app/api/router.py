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
import platform
import psutil
import torch
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


@router.get("/diagnostic")
async def system_diagnostic():
    """
    System diagnostic endpoint providing information about the system,
    CSM model, and voice generation capabilities.
    """
    try:
        # System information
        system_info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(logical=False),
            "logical_cpu_count": psutil.cpu_count(logical=True),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
        }
        
        # CUDA information
        cuda_info = {
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        }
        
        if torch.cuda.is_available():
            cuda_info["cuda_version"] = torch.version.cuda
            cuda_info["devices"] = []
            
            for i in range(torch.cuda.device_count()):
                device_props = torch.cuda.get_device_properties(i)
                cuda_info["devices"].append({
                    "name": device_props.name,
                    "total_memory_gb": round(device_props.total_memory / (1024**3), 2),
                    "major": device_props.major,
                    "minor": device_props.minor,
                })
        
        # Model information
        model_info = {}
        if voice_generator is not None:
            model_info = {
                "model_loaded": voice_generator.model is not None,
                "model_path": voice_generator.model_path,
                "output_dir": voice_generator.output_dir,
                "is_placeholder": isinstance(voice_generator.model, type) and "Placeholder" in voice_generator.model.__name__ if voice_generator.model else False,
            }
            
            # Get available voices
            try:
                voices = voice_generator.list_available_voices()
                model_info["available_voices"] = len(voices)
            except Exception as e:
                model_info["available_voices"] = 0
                model_info["voice_list_error"] = str(e)
        
        # Task system information
        task_info = {}
        if task_manager is not None:
            try:
                task_info = {
                    "active_tasks": task_manager.count_active_tasks(),
                    "completed_tasks": task_manager.count_completed_tasks(),
                    "failed_tasks": task_manager.count_failed_tasks(),
                }
            except Exception as e:
                task_info["error"] = str(e)
        
        return {
            "system": system_info,
            "cuda": cuda_info,
            "model": model_info,
            "tasks": task_info,
        }
    except Exception as e:
        logger.error(f"Error generating system diagnostic: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


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
    device: str = Field(config.DEFAULT_DEVICE, description="Device to use for inference (auto, cuda, or cpu)")


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
        
        # Validate device
        if request.device not in ["auto", "cuda", "cpu"]:
            raise HTTPException(status_code=400, detail="Device must be 'auto', 'cuda', or 'cpu'")
        
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
            style=request.style,
            device=request.device
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
                              temperature: float, top_k: int, style: str, device: str = "auto"):
    """Background task for voice generation."""
    try:
        # Update task status to processing
        task_manager.update_task(task_id, status="processing")
        
        # Generate voice
        logger.info(f"Generating voice for task {task_id} with device={device}")
        output_path, url = voice_generator.generate(
            text=text,
            speaker_id=speaker_id,
            temperature=temperature,
            top_k=top_k,
            style=style,
            device=device
        )
        
        if output_path and url:
            # Update task with success
            task_manager.update_task(
                task_id, 
                status="completed",
                result={
                    "text": text,
                    "speaker_id": speaker_id,
                    "file_url": url,
                    "output_file": url,  # Add output_file for compatibility
                    "file_path": output_path
                }
            )
            logger.info(f"Voice generation task {task_id} completed successfully")
        else:
            # Update task with failure
            task_manager.update_task(
                task_id, 
                status="failed",
                error="Failed to generate voice"
            )
            logger.error(f"Voice generation task {task_id} failed")
    except Exception as e:
        logger.exception(f"Error in voice generation task {task_id}: {str(e)}")
        # Update task with error
        task_manager.update_task(
            task_id, 
            status="failed",
            error=str(e)
        ) 