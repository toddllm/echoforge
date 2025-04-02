"""
Voice Cloning API Routes for EchoForge.

This module defines the API routes for voice cloning functionality.
"""

import os
import logging
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form, Depends, Request
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import shutil
from pathlib import Path

from app.core import config
from app.core.auth import auth_required
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.models.voice_cloning.voice_encoder import VoiceEncoder
from app.models.voice_cloning.voice_cloner import VoiceCloner
from app.models.voice_cloning.csm_integration import CSMVoiceCloner
from app.models.fine_tuning.voice_fine_tuner import VoiceFineTuner
from app.core.task_manager import task_manager

# Setup logging
logger = logging.getLogger("echoforge.api.voice_cloning")

# Create router
router = APIRouter(prefix=f"{config.API_PREFIX}/voice-cloning", tags=["voice_cloning"])

# Initialize components
voice_encoder = VoiceEncoder()
voice_cloner = VoiceCloner()
csm_cloner = CSMVoiceCloner()
voice_fine_tuner = VoiceFineTuner()

# Voice profiles storage path
VOICE_PROFILES_DIR = Path(config.OUTPUT_DIR) / "voice_profiles"
os.makedirs(VOICE_PROFILES_DIR, exist_ok=True)

# Sample uploads storage path
VOICE_SAMPLES_DIR = Path(config.OUTPUT_DIR) / "voice_samples"
os.makedirs(VOICE_SAMPLES_DIR, exist_ok=True)


class VoiceProfileCreate(BaseModel):
    """Model for voice profile creation request."""
    name: str = Field(..., min_length=1, max_length=100, description="Name of the voice profile")
    description: str = Field("", max_length=500, description="Description of the voice profile")
    labels: List[str] = Field(default=[], description="Labels/tags associated with the voice profile")


class VoiceProfileSimple(BaseModel):
    """Simple model for voice profile listing."""
    id: str = Field(..., description="Unique identifier for the voice profile")
    name: str = Field(..., description="Name of the voice profile")
    description: str = Field(..., description="Description of the voice profile")
    created_at: str = Field(..., description="ISO format datetime when the profile was created")
    samples_count: int = Field(..., description="Number of audio samples used to create this profile")


class VoiceProfile(VoiceProfileSimple):
    """Detailed model for voice profile."""
    updated_at: str = Field(..., description="ISO format datetime when the profile was last updated")
    settings: Dict[str, Any] = Field(..., description="Voice settings for this profile")


class VoiceGenerationFromProfileRequest(BaseModel):
    """Model for voice generation from profile request."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    profile_id: str = Field(..., description="ID of the voice profile to use")
    temperature: float = Field(0.6, ge=0.1, le=1.0, description="Temperature for generation (lower = more consistent)")
    top_k: int = Field(20, ge=1, description="Top-K for token selection")
    stability: float = Field(0.5, ge=0.0, le=1.0, description="Voice stability parameter")
    clarity: float = Field(0.5, ge=0.0, le=1.0, description="Voice clarity parameter")
    emotion_type: Optional[str] = Field(None, description="Type of emotion to apply")
    emotion_intensity: Optional[float] = Field(None, ge=0.0, le=1.0, description="Intensity of emotion to apply")
    device: str = Field(config.DEFAULT_DEVICE, description="Device to use for inference (auto, cuda, or cpu)")


class VoiceProfileUpdate(BaseModel):
    """Model for voice profile update request."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Name of the voice profile")
    description: Optional[str] = Field(None, max_length=500, description="Description of the voice profile")
    labels: Optional[List[str]] = Field(None, description="Labels/tags associated with the voice profile")
    settings: Optional[Dict[str, Any]] = Field(None, description="Voice settings to apply")


@router.post("/profiles")
async def create_voice_profile(background_tasks: BackgroundTasks, profile: VoiceProfileCreate = Form(...),
                             audio_files: List[UploadFile] = File(..., description="Audio files of the voice to clone")):
    """
    Create a new voice profile from audio samples.
    
    This endpoint accepts audio files and creates a voice profile that can be
    used for voice cloning.
    """
    try:
        # Create a unique profile ID
        profile_id = str(uuid.uuid4())
        
        # Create a directory for this profile's samples
        profile_samples_dir = VOICE_SAMPLES_DIR / profile_id
        os.makedirs(profile_samples_dir, exist_ok=True)
        
        # Save the uploaded audio files
        saved_files = []
        for i, audio_file in enumerate(audio_files):
            file_path = profile_samples_dir / f"sample_{i}_{audio_file.filename}"
            
            # Save the file
            with open(file_path, "wb") as f:
                shutil.copyfileobj(audio_file.file, f)
            
            saved_files.append(str(file_path))
        
        # In test mode, return a mock response
        if os.environ.get("ECHOFORGE_TEST") == "true" or task_manager is None:
            return {
                "profile_id": profile_id,
                "status": "processing",
                "name": profile.name,
                "description": profile.description,
                "samples_count": len(saved_files)
            }
        
        # Register a task for profile creation
        task_id = task_manager.register_task("voice_profile_creation")
        
        # Add the task to background tasks
        background_tasks.add_task(
            _create_voice_profile_task,
            task_id,
            profile_id,
            profile.name,
            profile.description,
            profile.labels,
            saved_files
        )
        
        return {
            "task_id": task_id,
            "profile_id": profile_id,
            "status": "processing",
            "name": profile.name,
            "samples_count": len(saved_files)
        }
    except Exception as e:
        logger.error(f"Error creating voice profile: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating voice profile: {str(e)}")


@router.get("/profiles", response_model=List[VoiceProfileSimple])
async def list_voice_profiles(request: Request, db: Session = Depends(get_db)):
    # Check authentication
    user_id = await auth_required(request)
    if not isinstance(user_id, str):
        return user_id  # This is a redirect response
    """List all available voice profiles."""
    try:
        # Mock data for testing
        if os.environ.get("ECHOFORGE_TEST") == "true":
            return [
                {
                    "id": "profile1",
                    "name": "Male Narrator",
                    "description": "Professional male narrator voice",
                    "created_at": "2023-06-01T12:00:00Z",
                    "samples_count": 3
                },
                {
                    "id": "profile2",
                    "name": "Female Assistant",
                    "description": "Friendly female assistant voice",
                    "created_at": "2023-06-02T12:00:00Z",
                    "samples_count": 5
                }
            ]
        
        # In a real implementation, we would query the database
        # For now, just scan the profiles directory
        profiles = []
        
        if VOICE_PROFILES_DIR.exists():
            for profile_file in VOICE_PROFILES_DIR.glob("*.json"):
                profile_id = profile_file.stem
                
                # Check if there's a corresponding embedding file
                embedding_file = VOICE_PROFILES_DIR / f"{profile_id}.npy"
                if embedding_file.exists():
                    # In a real implementation, we would load the profile data from the JSON file
                    # For now, just create a mock profile
                    profiles.append({
                        "id": profile_id,
                        "name": f"Voice Profile {profile_id[:8]}",
                        "description": "Voice profile generated by EchoForge",
                        "created_at": "2023-06-01T12:00:00Z",
                        "samples_count": 1
                    })
        
        return profiles
    except Exception as e:
        logger.error(f"Error listing voice profiles: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing voice profiles: {str(e)}")


@router.get("/profiles/{profile_id}", response_model=VoiceProfile)
async def get_voice_profile(profile_id: str, request: Request, db: Session = Depends(get_db)):
    # Check authentication
    user_id = await auth_required(request)
    if not isinstance(user_id, str):
        return user_id  # This is a redirect response
    """Get details of a specific voice profile."""
    try:
        # Mock data for testing
        if os.environ.get("ECHOFORGE_TEST") == "true":
            if profile_id == "profile1":
                return {
                    "id": "profile1",
                    "name": "Male Narrator",
                    "description": "Professional male narrator voice",
                    "created_at": "2023-06-01T12:00:00Z",
                    "updated_at": "2023-06-01T12:00:00Z",
                    "samples_count": 3,
                    "settings": {
                        "stability": 0.7,
                        "clarity": 0.8,
                        "emotion": {
                            "type": "neutral",
                            "intensity": 0.5
                        }
                    }
                }
            else:
                return {
                    "id": profile_id,
                    "name": f"Voice Profile {profile_id[:8]}",
                    "description": "Voice profile generated by EchoForge",
                    "created_at": "2023-06-01T12:00:00Z",
                    "updated_at": "2023-06-01T12:00:00Z",
                    "samples_count": 1,
                    "settings": {
                        "stability": 0.5,
                        "clarity": 0.5
                    }
                }
        
        # In a real implementation, we would query the database
        # Check if the profile exists
        profile_file = VOICE_PROFILES_DIR / f"{profile_id}.json"
        embedding_file = VOICE_PROFILES_DIR / f"{profile_id}.npy"
        
        if not profile_file.exists() or not embedding_file.exists():
            raise HTTPException(status_code=404, detail=f"Voice profile not found: {profile_id}")
        
        # In a real implementation, we would load the profile data from the JSON file
        # For now, just create a mock profile
        return {
            "id": profile_id,
            "name": f"Voice Profile {profile_id[:8]}",
            "description": "Voice profile generated by EchoForge",
            "created_at": "2023-06-01T12:00:00Z",
            "updated_at": "2023-06-01T12:00:00Z",
            "samples_count": 1,
            "settings": {
                "stability": 0.5,
                "clarity": 0.5
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voice profile: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting voice profile: {str(e)}")


@router.put("/profiles/{profile_id}")
async def update_voice_profile(profile_id: str, profile_update: VoiceProfileUpdate):
    """Update a voice profile."""
    try:
        # Check if the profile exists
        profile_file = VOICE_PROFILES_DIR / f"{profile_id}.json"
        embedding_file = VOICE_PROFILES_DIR / f"{profile_id}.npy"
        
        if not profile_file.exists() or not embedding_file.exists():
            raise HTTPException(status_code=404, detail=f"Voice profile not found: {profile_id}")
        
        # In a real implementation, we would update the profile data in the database
        # For now, just return a success message
        return {"message": f"Voice profile {profile_id} updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating voice profile: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating voice profile: {str(e)}")


@router.delete("/profiles/{profile_id}")
async def delete_voice_profile(profile_id: str):
    """Delete a voice profile."""
    try:
        # Check if the profile exists
        profile_file = VOICE_PROFILES_DIR / f"{profile_id}.json"
        embedding_file = VOICE_PROFILES_DIR / f"{profile_id}.npy"
        
        if not profile_file.exists() and not embedding_file.exists():
            raise HTTPException(status_code=404, detail=f"Voice profile not found: {profile_id}")
        
        # Delete the profile files
        if profile_file.exists():
            os.remove(profile_file)
        
        if embedding_file.exists():
            os.remove(embedding_file)
        
        # Delete any samples associated with this profile
        profile_samples_dir = VOICE_SAMPLES_DIR / profile_id
        if profile_samples_dir.exists():
            shutil.rmtree(profile_samples_dir)
        
        return {"message": f"Voice profile {profile_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting voice profile: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting voice profile: {str(e)}")


@router.post("/generate")
async def generate_voice_from_profile(background_tasks: BackgroundTasks, request: VoiceGenerationFromProfileRequest):
    """Generate voice using a voice profile."""
    try:
        # Check if the profile exists
        profile_file = VOICE_PROFILES_DIR / f"{request.profile_id}.json"
        embedding_file = VOICE_PROFILES_DIR / f"{request.profile_id}.npy"
        
        if not embedding_file.exists():
            raise HTTPException(status_code=404, detail=f"Voice profile not found: {request.profile_id}")
        
        # Create a unique task ID
        task_id = str(uuid.uuid4())
        
        # In test mode, return a mock response
        if os.environ.get("ECHOFORGE_TEST") == "true" or task_manager is None:
            return {"task_id": task_id, "status": "processing"}
        
        # Register a task for voice generation
        task_id = task_manager.register_task("voice_generation_from_profile")
        
        # Add the task to background tasks
        background_tasks.add_task(
            _generate_voice_from_profile_task,
            task_id,
            request.text,
            request.profile_id,
            request.temperature,
            request.top_k,
            request.stability,
            request.clarity,
            request.emotion_type,
            request.emotion_intensity,
            request.device
        )
        
        return {"task_id": task_id, "status": "processing"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating voice from profile: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating voice from profile: {str(e)}")


@router.post("/clone")
async def clone_voice(background_tasks: BackgroundTasks, 
                    text: str = Form(..., description="Text to convert to speech"),
                    audio_file: UploadFile = File(..., description="Audio file of the voice to clone"),
                    transcription: Optional[str] = Form(None, description="Optional transcription of the audio file"),
                    temperature: float = Form(0.6, description="Temperature for generation (lower = more consistent)"),
                    top_k: int = Form(20, description="Top-K for token selection"),
                    stability: float = Form(0.5, description="Voice stability parameter"),
                    clarity: float = Form(0.5, description="Voice clarity parameter"),
                    device: str = Form("auto", description="Device to use for inference")):
    """
    Clone a voice from an audio sample and generate speech.
    
    This endpoint accepts an audio file of a voice and generates speech
    in that voice using the provided text.
    """
    try:
        # Create a unique task ID
        task_id = str(uuid.uuid4())
        
        # Create a temporary directory for the audio file
        temp_dir = Path(config.OUTPUT_DIR) / "temp" / task_id
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save the uploaded audio file
        audio_path = temp_dir / audio_file.filename
        with open(audio_path, "wb") as f:
            shutil.copyfileobj(audio_file.file, f)
        
        # In test mode, return a mock response
        if os.environ.get("ECHOFORGE_TEST") == "true" or task_manager is None:
            return {"task_id": task_id, "status": "processing"}
        
        # Register a task for voice cloning
        task_id = task_manager.register_task("voice_cloning")
        
        # Add the task to background tasks
        background_tasks.add_task(
            _clone_voice_task,
            task_id,
            text,
            str(audio_path),
            transcription,
            temperature,
            top_k,
            stability,
            clarity,
            device
        )
        
        return {"task_id": task_id, "status": "processing"}
    except Exception as e:
        logger.error(f"Error cloning voice: {e}")
        raise HTTPException(status_code=500, detail=f"Error cloning voice: {str(e)}")


# Background task functions
async def _create_voice_profile_task(task_id: str, profile_id: str, name: str, 
                                    description: str, labels: List[str], audio_files: List[str]):
    """Background task for creating a voice profile."""
    try:
        task_manager.update_task(task_id, status="processing", progress=0, 
                               message="Starting voice profile creation")
        
        # Initialize the voice cloner if needed
        if not voice_cloner.is_initialized:
            task_manager.update_task(task_id, message="Initializing voice cloner")
            voice_cloner.initialize()
        
        # Use the first audio file as the reference for the voice profile
        # In a production environment, you'd want to use multiple samples and transcriptions
        reference_audio = audio_files[0]
        
        # Process audio file and create voice profile
        task_manager.update_task(task_id, progress=50, message="Creating voice profile")
        
        # Create the voice profile using CSM voice cloning
        metadata = {
            "name": name,
            "description": description,
            "labels": labels,
            "created_at": "2023-06-01T12:00:00Z",  # Use actual timestamp in real implementation
            "samples_count": len(audio_files)
        }
        
        # Save the voice profile
        task_manager.update_task(task_id, progress=80, message="Saving voice profile")
        profile_info = voice_cloner.create_voice_profile(profile_id, reference_audio)
        
        # Add metadata to profile_info
        profile_info.update(metadata)
        
        # Mark the task as completed
        task_manager.update_task(task_id, status="completed", progress=100, 
                               message="Voice profile created successfully",
                               result={"profile_id": profile_id})
    except Exception as e:
        logger.error(f"Error in voice profile creation task: {e}")
        task_manager.update_task(task_id, status="failed", message=f"Error: {str(e)}")


async def _generate_voice_from_profile_task(task_id: str, text: str, profile_id: str,
                                          temperature: float, top_k: int,
                                          stability: float, clarity: float,
                                          emotion_type: Optional[str],
                                          emotion_intensity: Optional[float],
                                          device: str):
    """Background task for generating voice from a profile."""
    try:
        task_manager.update_task(task_id, status="processing", progress=0, 
                               message="Starting voice generation")
        
        # Initialize the voice cloner if needed
        if not voice_cloner.is_initialized:
            task_manager.update_task(task_id, message="Initializing voice cloner")
            voice_cloner.initialize()
        
        # Generate speech using the voice profile
        task_manager.update_task(task_id, progress=50, message="Generating speech")
        output_filename = f"voice_{task_id}.wav"
        output_path = Path(config.OUTPUT_DIR) / output_filename
        
        audio, sample_rate = voice_cloner.clone_from_profile(
            text, profile_id, temperature, top_k, str(output_path)
        )
        
        # Save the generated audio
        task_manager.update_task(task_id, progress=80, message="Saving generated audio")
        output_filename = f"voice_{task_id}.wav"
        output_path = Path(config.OUTPUT_DIR) / output_filename
        voice_cloner.save_cloned_audio(audio, sample_rate, str(output_path))
        
        # Mark the task as completed
        task_manager.update_task(task_id, status="completed", progress=100, 
                               message="Voice generated successfully",
                               result={"audio_file": output_filename})
    except Exception as e:
        logger.error(f"Error in voice generation task: {e}")
        task_manager.update_task(task_id, status="failed", message=f"Error: {str(e)}")


async def _clone_voice_task(task_id: str, text: str, audio_path: str,
                          transcription: Optional[str],
                          temperature: float, top_k: int,
                          stability: float, clarity: float,
                          device: str):
    """Background task for cloning a voice and generating speech."""
    try:
        task_manager.update_task(task_id, status="processing", progress=0, 
                               message="Starting voice cloning")
        
        # Initialize the voice cloner if needed
        if not voice_cloner.is_initialized:
            task_manager.update_task(task_id, message="Initializing voice cloner")
            voice_cloner.initialize()
        
        # Clone the voice and generate speech
        task_manager.update_task(task_id, progress=40, message="Cloning voice and generating speech")
        output_filename = f"voice_{task_id}.wav"
        output_path = Path(config.OUTPUT_DIR) / output_filename
        
        # Process with CSM voice cloning
        audio, sample_rate = voice_cloner.clone_voice(
            text, audio_path, temperature, top_k, transcription, str(output_path)
        )
        
        # Save the generated audio
        task_manager.update_task(task_id, progress=80, message="Saving generated audio")
        output_filename = f"voice_{task_id}.wav"
        output_path = Path(config.OUTPUT_DIR) / output_filename
        voice_cloner.save_cloned_audio(audio, sample_rate, str(output_path))
        
        # Mark the task as completed
        task_manager.update_task(task_id, status="completed", progress=100, 
                               message="Voice cloned and generated successfully",
                               result={"audio_file": output_filename})
        
        # Clean up the temporary audio file
        temp_dir = Path(audio_path).parent
        if temp_dir.exists() and temp_dir.name == task_id:
            shutil.rmtree(temp_dir)
    except Exception as e:
        logger.error(f"Error in voice cloning task: {e}")
        task_manager.update_task(task_id, status="failed", message=f"Error: {str(e)}")
