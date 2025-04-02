"""
V1 API compatibility module for EchoForge.

This module provides backward compatibility with v1 API endpoints.
"""

from fastapi import APIRouter, Request, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging
from typing import Dict, Any, Optional
import os

from app.api.voice_routes import generate_voice, VoiceGenerationRequest, get_task_status

# Setup logging
logger = logging.getLogger("echoforge.api.v1")

# Create router for v1 API
router = APIRouter(prefix="/v1", tags=["v1"])

# Define compatibility route for generate
@router.post("/generate")
async def generate_v1(
    background_tasks: BackgroundTasks, 
    request: Request
):
    """
    V1 compatibility route for voice generation.
    Maps older API requests to the current voice generation endpoint.
    """
    try:
        # Parse JSON from request
        json_data = await request.json()
        logger.info(f"Received v1 API request: {json_data}")
        
        # Get speaker_id, ensure it's at least 1 (v1 API used 0-based indexing)
        speaker_id = json_data.get("speaker_id", 1)
        if speaker_id == 0:
            speaker_id = 1  # Map speaker 0 to speaker 1 for compatibility
        
        # Map v1 request format to current format
        generation_request = VoiceGenerationRequest(
            text=json_data.get("text", ""),
            speaker_id=speaker_id,
            temperature=json_data.get("temperature", 0.7),
            top_k=json_data.get("top_k", 50),
            style=json_data.get("style", "default"),
            device=json_data.get("device", "auto")
        )
        
        logger.info(f"Mapped to VoiceGenerationRequest: {generation_request}")
        
        # Call the current generate_voice function
        return await generate_voice(background_tasks, generation_request)
    except Exception as e:
        logger.error(f"Error in v1 generate endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to process request: {str(e)}"}
        )

# Define compatibility route for task status
@router.get("/tasks/{task_id}")
async def task_status_v1(task_id: str):
    """
    V1 compatibility route for checking task status.
    Maps to the current task status endpoint.
    """
    try:
        logger.info(f"Received v1 API task status request for task: {task_id}")
        
        # Call the current get_task_status function
        result = await get_task_status(task_id)
        
        # Return the result as is
        return result
    except Exception as e:
        logger.error(f"Error in v1 task status endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get task status: {str(e)}"}
        ) 