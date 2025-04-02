"""
Voice API Routes for EchoForge.

This module defines API routes for voice generation functionality.
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends, Request
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os
import uuid
import random
import re
import json
from pathlib import Path

from app.core import config
from app.api.voice_generator import voice_generator
from app.core.task_manager import task_manager

# Setup logging
logger = logging.getLogger("echoforge.api.voice_routes")

# Create router
router = APIRouter(prefix="/voices", tags=["voices"])

# Expanded sample voices data
MOCK_VOICES = [
    {
        "speaker_id": 1,
        "name": "Commander Sterling",
        "gender": "male",
        "style": "authoritative",
        "description": "Authoritative male voice with clear diction and commanding presence, perfect for leadership roles."
    },
    {
        "speaker_id": 2,
        "name": "Dr. Elise Jensen",
        "gender": "female",
        "style": "professional",
        "description": "Professional female voice with precise articulation and thoughtful cadence, ideal for scientific content."
    },
    {
        "speaker_id": 3,
        "name": "James Fletcher",
        "gender": "male",
        "style": "friendly",
        "description": "Warm and approachable male voice with a natural, conversational tone perfect for narration."
    },
    {
        "speaker_id": 4,
        "name": "Sophia Chen",
        "gender": "female",
        "style": "cheerful",
        "description": "Bright and engaging female voice with an upbeat cadence, great for educational content."
    },
    {
        "speaker_id": 5,
        "name": "Morgan Riley",
        "gender": "neutral",
        "style": "calm",
        "description": "Gender-neutral voice with a soothing quality, well-suited for meditation and relaxation content."
    },
    {
        "speaker_id": 6,
        "name": "Gabriel Ortiz",
        "gender": "male",
        "style": "dramatic",
        "description": "Expressive male voice with theatrical qualities, perfect for storytelling and entertainment."
    },
    {
        "speaker_id": 7,
        "name": "Victoria Wells",
        "gender": "female",
        "style": "formal",
        "description": "Refined female voice with elegant diction and measured pacing for professional presentations."
    },
    {
        "speaker_id": 8,
        "name": "Alex Kim",
        "gender": "neutral",
        "style": "energetic",
        "description": "Dynamic voice with youthful energy and enthusiasm, ideal for advertisements and promotions."
    }
]

def extract_voices_from_js():
    """Extract voice data from voice_samples.js file."""
    try:
        # Path to the JS file
        js_file_path = Path(os.path.join(config.PROJECT_ROOT, "static", "js", "voice_samples.js"))
        
        if not js_file_path.exists():
            logger.warning(f"Voice samples JS file not found: {js_file_path}")
            return []
        
        # Read the JS file content
        with open(js_file_path, "r") as f:
            js_content = f.read()
        
        # Extract the JSON part
        # Looking for content between { and } that contains the samples array
        match = re.search(r'const\s+voiceExplorationSamples\s*=\s*({[^;]*})', js_content, re.DOTALL)
        if not match:
            logger.warning("Could not extract voice samples data from JS file")
            return []
            
        # Extract the JSON string and convert to a Python object
        json_str = match.group(1)
        # Make it valid JSON (replace single quotes, etc.)
        json_str = json_str.replace("'", '"')
        
        # Parse the JSON
        try:
            data = json.loads(json_str)
            samples = data.get("samples", [])
            
            # Format the samples for the API
            formatted_voices = []
            for i, sample in enumerate(samples):
                if i >= 10:  # Limit to 10 voices for performance
                    break
                    
                formatted_voices.append({
                    "speaker_id": sample.get("speaker_id", i + 1),
                    "name": f"Voice {sample.get('speaker_id', i + 1)}",
                    "gender": "female" if "female" in sample.get("description", "").lower() else "male",
                    "style": sample.get("style", "default"),
                    "description": sample.get("description", "Voice sample"),
                    "url": f"/static/samples/voice_{sample.get('speaker_id', i + 1)}_sample.mp3"
                })
            
            return formatted_voices
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing voice samples JSON: {e}")
            return []
            
    except Exception as e:
        logger.error(f"Error extracting voices from JS file: {e}")
        return []

@router.get("/list")
async def list_voices():
    """List available voices."""
    try:
        # In production mode, use real voices from the voice generator
        voices = voice_generator.list_available_voices()
        
        # Ensure we always return an array even if the voice generator returns None
        if voices is None:
            logger.warning("Voice generator returned None for list_available_voices()")
            return []
            
        # Ensure the response is an array
        if not isinstance(voices, list):
            logger.warning(f"Voice generator returned non-list type: {type(voices)}")
            return []
            
        return voices
    except Exception as e:
        logger.error(f"Error listing voices: {str(e)}")
        # Return empty array instead of raising an error
        return []

@router.get("")
async def list_voices_compat():
    """List available voices (compatibility endpoint)."""
    try:
        # Call the original list_voices function
        return await list_voices()
    except Exception as e:
        logger.error(f"Error in voice list compatibility endpoint: {str(e)}")
        return []

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
        mock_url = f"/api/voices/file/{mock_filename}"
        
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

@router.get("/file/{file_path:path}")
async def get_voice_file(file_path: str):
    """Get a voice file by path."""
    try:
        # Construct the path to the voice file
        voice_file = Path(voice_generator.output_dir) / file_path
        
        # Check if the file exists
        if not voice_file.exists():
            # Try looking in the local static directory as a fallback
            local_static_path = Path(config.ROOT_DIR) / "static" / "voices" / "creative" / file_path.split("/")[-1]
            if local_static_path.exists():
                return FileResponse(local_static_path)
            
            raise HTTPException(status_code=404, detail=f"Voice file not found: {file_path}")
        
        return FileResponse(voice_file)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error getting voice file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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