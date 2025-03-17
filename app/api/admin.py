"""
Admin API for EchoForge.

This module defines the admin API routes for the EchoForge application.
"""

import logging
import os
import psutil
import platform
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import time
import uuid
import shutil

from app.core import config
from app.core.auth import verify_credentials
from app.api.voice_generator import voice_generator
from app.core.task_manager import TaskManager
from app.models import create_direct_csm, DirectCSMError

# Try to import optional components
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from app.api.voice_generator import voice_generator
except ImportError:
    voice_generator = None

try:
    from app.core.task_manager import task_manager
except ImportError:
    task_manager = None

# Setup logging
logger = logging.getLogger("echoforge.admin")

# Create router
router = APIRouter(prefix="/api/admin", tags=["admin"])

# Initialize task manager
task_manager = TaskManager()

# Models
class SystemStats(BaseModel):
    """System statistics model."""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    gpu_usage: Optional[float] = None
    gpu_memory: Optional[float] = None
    uptime: float
    model_loaded: bool
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_voices: int


class ModelInfo(BaseModel):
    """Model information."""
    name: str
    status: str
    device: str
    memory_usage: Optional[float] = None
    loaded_at: Optional[datetime] = None


class TaskInfo(BaseModel):
    """Task information."""
    task_id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    progress: float
    text: str
    speaker_id: int
    parameters: Dict[str, Any]


class ConfigSetting(BaseModel):
    """Configuration setting."""
    key: str
    value: Any
    description: str
    editable: bool


class LogEntry(BaseModel):
    """Log entry."""
    timestamp: datetime
    level: str
    message: str
    source: str


class VoiceInfo(BaseModel):
    """Voice information."""
    id: int
    name: str
    gender: str
    style: str
    sample_count: int
    file_path: str


# Endpoints
@router.get("/stats", response_model=SystemStats)
async def get_system_stats(username: str = Depends(verify_credentials)):
    """Get system statistics."""
    logger.info(f"Getting system stats for user: {username}")
    
    # Get CPU usage
    cpu_usage = psutil.cpu_percent(interval=0.1)
    
    # Get memory usage
    memory = psutil.virtual_memory()
    memory_usage = memory.percent
    
    # Get disk usage
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent
    
    # Get GPU usage if available
    gpu_usage = None
    gpu_memory = None
    if HAS_TORCH and torch.cuda.is_available():
        try:
            # This is a placeholder - actual GPU monitoring would require additional libraries
            gpu_usage = 0.0
            gpu_memory = 0.0
        except Exception as e:
            logger.error(f"Error getting GPU stats: {str(e)}")
    
    # Get uptime
    uptime = psutil.boot_time()
    uptime_seconds = datetime.now().timestamp() - uptime
    
    # Get model status
    model_loaded = voice_generator is not None
    
    # Get task stats
    active_tasks = 0
    completed_tasks = 0
    failed_tasks = 0
    if task_manager:
        try:
            tasks = task_manager.get_all_tasks()
            active_tasks = sum(1 for t in tasks.values() if t.get('status') == 'processing')
            completed_tasks = sum(1 for t in tasks.values() if t.get('status') == 'completed')
            failed_tasks = sum(1 for t in tasks.values() if t.get('status') == 'failed')
        except AttributeError:
            # TaskManager doesn't have get_all_tasks method in test environment
            logger.warning("TaskManager.get_all_tasks not available, using default values")
            active_tasks = 0
            completed_tasks = 0
            failed_tasks = 0
    
    # Get voice count
    total_voices = 10  # Placeholder - should be retrieved from actual voice data
    
    return SystemStats(
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        disk_usage=disk_usage,
        gpu_usage=gpu_usage,
        gpu_memory=gpu_memory,
        uptime=uptime_seconds,
        model_loaded=model_loaded,
        active_tasks=active_tasks,
        completed_tasks=completed_tasks,
        failed_tasks=failed_tasks,
        total_voices=total_voices
    )


@router.get("/models", response_model=List[ModelInfo])
async def get_models(username: str = Depends(verify_credentials)):
    """Get model information."""
    logger.info(f"Getting model info for user: {username}")
    
    models = []
    
    # Add CSM model info if available
    if voice_generator and voice_generator.is_initialized():
        device = "cpu"
        if HAS_TORCH and torch.cuda.is_available() and voice_generator.device == "cuda":
            device = f"cuda:{torch.cuda.current_device()} ({torch.cuda.get_device_name(0)})"
        
        # Check if using direct CSM
        model_name = "CSM Model"
        if voice_generator.direct_csm is not None:
            model_name = "Direct CSM Model"
        
        models.append(ModelInfo(
            name=model_name,
            status="Loaded",
            device=device,
            memory_usage=None,  # Would require additional monitoring
            loaded_at=datetime.now()  # Placeholder - should be actual load time
        ))
    else:
        # Check if direct CSM is enabled in config
        model_name = "CSM Model"
        if config.USE_DIRECT_CSM:
            model_name = "Direct CSM Model"
            
        models.append(ModelInfo(
            name=model_name,
            status="Not Loaded",
            device="None",
            memory_usage=None,
            loaded_at=None
        ))
    
    return models


@router.post("/models/{model_name}/load")
async def load_model(
    model_name: str, 
    background_tasks: BackgroundTasks,
    username: str = Depends(verify_credentials)
):
    """Load a model."""
    logger.info(f"Loading model {model_name} for user: {username}")
    
    if not voice_generator:
        raise HTTPException(status_code=500, detail="Voice generator not available")
    
    if voice_generator.is_initialized():
        return {"status": "already_loaded", "message": "Model is already loaded"}
    
    # Start loading the model in the background
    background_tasks.add_task(voice_generator.initialize)
    
    return {"status": "loading", "message": "Model loading started"}


@router.post("/models/{model_name}/unload")
async def unload_model(
    model_name: str,
    username: str = Depends(verify_credentials)
):
    """Unload a model."""
    logger.info(f"Unloading model {model_name} for user: {username}")
    
    if not voice_generator:
        raise HTTPException(status_code=500, detail="Voice generator not available")
    
    if not voice_generator.is_initialized():
        return {"status": "not_loaded", "message": "Model is not loaded"}
    
    # Unload the model
    voice_generator.shutdown()
    
    return {"status": "unloaded", "message": "Model unloaded successfully"}


@router.get("/tasks", response_model=List[TaskInfo])
async def get_tasks(username: str = Depends(verify_credentials)):
    """Get all tasks."""
    logger.info(f"Getting tasks for user: {username}")
    
    # Get all tasks from the task manager
    tasks = task_manager.get_all_tasks()
    
    # Convert to TaskInfo objects
    task_infos = []
    for task_id, task in tasks.items():
        task_infos.append(TaskInfo(
            task_id=task_id,
            status=task.status,
            created_at=task.created_at,
            completed_at=task.completed_at,
            progress=task.progress,
            text=task.text if hasattr(task, 'text') else "",
            speaker_id=task.speaker_id if hasattr(task, 'speaker_id') else 1,
            parameters=task.parameters if hasattr(task, 'parameters') else {}
        ))
    
    # Sort by created_at (newest first)
    task_infos.sort(key=lambda x: x.created_at, reverse=True)
    
    return task_infos


@router.post("/tasks/{task_id}", response_model=dict)
async def get_task_status(
    task_id: str,
    username: str = Depends(verify_credentials)
):
    """Get task status by ID."""
    logger.info(f"Getting task status for task {task_id} for user: {username}")
    
    # Get task from the task manager
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Return task status - handle both object and dictionary formats
    if isinstance(task, dict):
        return {
            "task_id": task_id,
            "status": task.get("status", "unknown"),
            "progress": task.get("progress", 0),
            "created_at": task.get("created_at"),
            "updated_at": task.get("updated_at"),
            "completed_at": task.get("completed_at"),
            "result": task.get("result"),
            "error": task.get("error"),
            "device_info": task.get("device_info"),
            "message": task.get("message")
        }
    else:
        return {
            "task_id": task_id,
            "status": getattr(task, "status", "unknown"),
            "progress": getattr(task, "progress", 0),
            "created_at": getattr(task, "created_at", None),
            "updated_at": getattr(task, "updated_at", None),
            "completed_at": getattr(task, "completed_at", None),
            "result": getattr(task, "result", None) if hasattr(task, "result") else None,
            "error": getattr(task, "error", None) if hasattr(task, "error") else None,
            "device_info": getattr(task, "device_info", None) if hasattr(task, "device_info") else None,
            "message": getattr(task, "message", None) if hasattr(task, "message") else None
        }


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    username: str = Depends(verify_credentials)
):
    """Delete a task."""
    logger.info(f"Deleting task {task_id} for user: {username}")
    
    # Delete task from the task manager
    success = task_manager.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"status": "deleted"}


@router.get("/config", response_model=List[ConfigSetting])
async def get_config(username: str = Depends(verify_credentials)):
    """Get configuration settings."""
    logger.info(f"Getting config for user: {username}")
    
    # Get configuration settings from config module
    settings = []
    
    # Add settings that can be edited
    settings.append(ConfigSetting(
        key="DEFAULT_TEMPERATURE",
        value=config.DEFAULT_TEMPERATURE,
        description="Default temperature for voice generation",
        editable=True
    ))
    
    settings.append(ConfigSetting(
        key="DEFAULT_TOP_K",
        value=config.DEFAULT_TOP_K,
        description="Default top-k value for voice generation",
        editable=True
    ))
    
    settings.append(ConfigSetting(
        key="DEFAULT_SPEAKER_ID",
        value=config.DEFAULT_SPEAKER_ID,
        description="Default speaker ID for voice generation",
        editable=True
    ))
    
    settings.append(ConfigSetting(
        key="DEFAULT_STYLE",
        value=config.DEFAULT_STYLE,
        description="Default voice style",
        editable=True
    ))
    
    settings.append(ConfigSetting(
        key="DEFAULT_DEVICE",
        value=config.DEFAULT_DEVICE,
        description="Default device for inference (auto, cuda, or cpu)",
        editable=True
    ))
    
    settings.append(ConfigSetting(
        key="DEFAULT_THEME",
        value=config.DEFAULT_THEME,
        description="Default UI theme (light or dark)",
        editable=True
    ))
    
    # Add read-only settings
    settings.append(ConfigSetting(
        key="APP_NAME",
        value=config.APP_NAME,
        description="Application name",
        editable=False
    ))
    
    settings.append(ConfigSetting(
        key="APP_VERSION",
        value=config.APP_VERSION,
        description="Application version",
        editable=False
    ))
    
    settings.append(ConfigSetting(
        key="OUTPUT_DIR",
        value=config.OUTPUT_DIR,
        description="Output directory for generated voices",
        editable=False
    ))
    
    return settings


@router.put("/config/{key}")
async def update_config(
    key: str,
    value: Any,
    username: str = Depends(verify_credentials)
):
    """Update a configuration setting."""
    logger.info(f"Updating config {key} to {value} for user: {username}")
    
    # Check if setting exists and is editable
    editable_settings = [
        "DEFAULT_TEMPERATURE",
        "DEFAULT_TOP_K",
        "DEFAULT_SPEAKER_ID",
        "DEFAULT_STYLE",
        "DEFAULT_DEVICE",
        "DEFAULT_THEME"
    ]
    
    if key not in editable_settings:
        raise HTTPException(status_code=400, detail="Setting not found or not editable")
    
    # Update the setting (in a real implementation, this would update the .env file)
    # For now, we'll just log the change
    logger.info(f"Would update {key} to {value}")
    
    return {"status": "updated", "message": f"Setting {key} updated to {value}"}


@router.get("/logs", response_model=List[LogEntry])
async def get_logs(
    limit: int = 100,
    level: Optional[str] = None,
    source: Optional[str] = None,
    username: str = Depends(verify_credentials)
):
    """Get application logs."""
    logger.info(f"Getting logs for user: {username}")
    
    # In a real implementation, this would read from log files
    # For now, we'll return mock data
    logs = []
    
    # Add some mock log entries
    logs.append(LogEntry(
        timestamp=datetime.now(),
        level="INFO",
        message="Application started",
        source="app.main"
    ))
    
    logs.append(LogEntry(
        timestamp=datetime.now(),
        level="INFO",
        message="Model loaded successfully",
        source="app.api.voice_generator"
    ))
    
    logs.append(LogEntry(
        timestamp=datetime.now(),
        level="WARNING",
        message="High CPU usage detected",
        source="app.core.monitoring"
    ))
    
    # Filter by level if provided
    if level:
        logs = [log for log in logs if log.level == level]
    
    # Filter by source if provided
    if source:
        logs = [log for log in logs if source in log.source]
    
    # Apply limit
    logs = logs[:limit]
    
    return logs


@router.get("/voices", response_model=List[VoiceInfo])
async def get_voices(username: str = Depends(verify_credentials)):
    """Get voice information."""
    logger.info(f"Getting voices for user: {username}")
    
    # In a real implementation, this would read from the voice database
    # For now, we'll return mock data
    voices = []
    
    # Add some mock voice entries
    voices.append(VoiceInfo(
        id=1,
        name="Male Voice 1",
        gender="male",
        style="default",
        sample_count=10,
        file_path="/path/to/sample1.wav"
    ))
    
    voices.append(VoiceInfo(
        id=2,
        name="Female Voice 1",
        gender="female",
        style="default",
        sample_count=8,
        file_path="/path/to/sample2.wav"
    ))
    
    voices.append(VoiceInfo(
        id=3,
        name="Child Voice 1",
        gender="child",
        style="default",
        sample_count=5,
        file_path="/path/to/sample3.wav"
    ))
    
    return voices


@router.post("/generate-voice")
async def admin_generate_voice(
    background_tasks: BackgroundTasks,
    username: str = Depends(verify_credentials),
    text: str = Body(..., embed=True),
    speaker_id: int = Body(1, embed=True),
    temperature: float = Body(0.7, embed=True),
    top_k: int = Body(50, embed=True),
    style: str = Body("natural", embed=True),
    device: str = Body("cuda", embed=True),
    reload_model: bool = Body(False, embed=True)
):
    """Generate a voice using the admin API."""
    logger.info(f"Admin voice generation request from user: {username}")
    
    # Validate parameters
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    if temperature < 0.1 or temperature > 1.0:
        raise HTTPException(status_code=400, detail="Temperature must be between 0.1 and 1.0")
    
    if top_k < 1 or top_k > 100:
        raise HTTPException(status_code=400, detail="Top-K must be between 1 and 100")
    
    # Register a task and get the task_id
    task_id = task_manager.register_task("admin_voice_generation")
    
    # Start the generation in the background
    background_tasks.add_task(
        _generate_admin_voice,
        task_id=task_id,
        text=text,
        speaker_id=speaker_id,
        temperature=temperature,
        top_k=top_k,
        style=style,
        device=device,
        reload_model=reload_model
    )
    
    return {"task_id": task_id, "status": "started"}


async def _generate_admin_voice(task_id: str, text: str, speaker_id: int, temperature: float, top_k: int, style: str, device: str, reload_model: bool = False):
    """Generate a voice in the background."""
    logger.info(f"Starting admin voice generation for task {task_id}")
    
    try:
        # Update task status with device info
        task_manager.update_task(
            task_id, 
            status="processing", 
            progress=10,
            device_info=f"Using device: {device}"
        )
        
        # Generate the voice
        if not voice_generator:
            raise Exception("Voice generator not available")
        
        # Log GPU info if using CUDA
        if device == "cuda" and torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            free_memory = torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)
            free_memory_gb = free_memory / (1024 ** 3)
            logger.info(f"Using GPU: {gpu_name} with {free_memory_gb:.2f} GB free memory for task {task_id}")
            
            # Update task with GPU info
            task_manager.update_task(
                task_id,
                status="processing",
                progress=20,
                device_info=f"Using GPU: {gpu_name} with {free_memory_gb:.2f} GB free memory"
            )
        
        # Update progress before generation
        task_manager.update_task(task_id, status="processing", progress=30, message="Starting voice synthesis")
        
        # Generate the voice
        output_file = voice_generator.generate_voice(
            text=text,
            speaker_id=speaker_id,
            temperature=temperature,
            top_k=top_k,
            style=style,
            device=device,
            reload_model=reload_model
        )
        
        # Update progress after generation
        task_manager.update_task(task_id, status="processing", progress=70, message="Voice synthesis complete")
        
        if not output_file:
            raise Exception("Voice generation failed")
        
        # Copy the file to the admin directory
        admin_dir = os.path.join(config.OUTPUT_DIR, "admin")
        os.makedirs(admin_dir, exist_ok=True)
        
        filename = os.path.basename(output_file)
        admin_file = os.path.join(admin_dir, filename)
        shutil.copy2(output_file, admin_file)
        
        logger.info(f"Copied voice file to admin directory: {admin_file}")
        
        # Update progress after file copy
        task_manager.update_task(task_id, status="processing", progress=90, message="Finalizing audio file")
        
        # Create a URL for the file
        file_url = f"/api/admin/voices/{filename}"
        
        # Update task status
        task_manager.update_task(
            task_id,
            status="completed",
            progress=100,
            result={"file_url": file_url, "filename": filename}
        )
        
        logger.info(f"Admin voice generation completed for task {task_id}: {admin_file}")
        
    except Exception as e:
        logger.error(f"Voice generation failed for task {task_id}")
        logger.exception(e)
        
        # Update task status
        task_manager.update_task(
            task_id,
            status="failed",
            progress=100,
            error=str(e)
        )


@router.get("/voices/{filename}")
async def get_voice_file(filename: str, username: str = Depends(verify_credentials)):
    """Get a generated voice file."""
    logger.info(f"Request for voice file: {filename} from user: {username}")
    
    # Define the path to the admin voices directory
    admin_voices_dir = os.path.join(config.OUTPUT_DIR, "admin")
    file_path = os.path.join(admin_voices_dir, filename)
    
    # Check if the file exists
    if not os.path.exists(file_path):
        logger.error(f"Voice file not found: {file_path}")
        raise HTTPException(status_code=404, detail="Voice file not found")
    
    # Log the file path that's being served
    logger.info(f"Serving voice file: {file_path}")
    
    # Serve the file
    return FileResponse(
        file_path, 
        media_type="audio/wav",
        filename=filename
    )


@router.post("/models/toggle-direct-csm")
async def toggle_direct_csm(
    username: str = Depends(verify_credentials),
    enable: bool = Body(..., embed=True)
):
    """Toggle direct CSM implementation."""
    logger.info(f"Toggling direct CSM to {enable} for user: {username}")
    
    if not voice_generator:
        raise HTTPException(status_code=500, detail="Voice generator not available")
    
    # Update the config
    config.USE_DIRECT_CSM = enable
    
    # Update the voice generator
    voice_generator.use_direct_csm = enable
    
    # If the model is already loaded, we need to reload it
    if voice_generator.is_initialized():
        # Unload the current model
        if hasattr(voice_generator, 'cleanup'):
            voice_generator.cleanup()
        else:
            voice_generator.model = None
            voice_generator.direct_csm = None
        
        # Reload the model
        try:
            voice_generator.load_model()
            return {
                "status": "success",
                "message": f"Direct CSM {'enabled' if enable else 'disabled'} and model reloaded",
                "direct_csm_enabled": enable
            }
        except Exception as e:
            logger.error(f"Error reloading model after toggling direct CSM: {e}")
            return {
                "status": "error",
                "message": f"Error reloading model: {str(e)}",
                "direct_csm_enabled": enable
            }
    
    return {
        "status": "success",
        "message": f"Direct CSM {'enabled' if enable else 'disabled'}",
        "direct_csm_enabled": enable
    }


@router.post("/models/test-direct-csm")
async def test_direct_csm(
    background_tasks: BackgroundTasks,
    username: str = Depends(verify_credentials)
):
    """Test direct CSM implementation."""
    logger.info(f"Testing direct CSM for user: {username}")
    
    if not voice_generator:
        raise HTTPException(status_code=500, detail="Voice generator not available")
    
    # Check if direct CSM is enabled
    if not config.USE_DIRECT_CSM:
        return {
            "status": "error",
            "message": "Direct CSM is not enabled. Please enable it first."
        }
    
    # Generate a test task
    task_id = task_manager.register_task("test_direct_csm")
    
    # Launch background task for testing
    background_tasks.add_task(
        _test_direct_csm,
        task_id=task_id
    )
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Direct CSM test has been started"
    }


async def _test_direct_csm(task_id: str):
    """Background task for testing direct CSM."""
    logger.info(f"Starting direct CSM test for task {task_id}")
    
    try:
        # Update task status
        task_manager.update_task(task_id, status="processing")
        
        # Test text
        test_text = "This is a test of the direct CSM implementation. The voice should be clear and natural sounding."
        
        # Create a direct CSM instance
        try:
            # Create and initialize direct CSM
            direct_csm = create_direct_csm(model_path=config.MODEL_PATH)
            direct_csm.initialize()
            
            # Generate speech
            audio, sample_rate = direct_csm.generate_speech(
                text=test_text,
                speaker_id=config.DEFAULT_SPEAKER_ID,
                temperature=config.DEFAULT_TEMPERATURE,
                top_k=config.DEFAULT_TOP_K
            )
            
            # Create a test output directory
            test_output_dir = os.path.join(config.OUTPUT_DIR, "test")
            os.makedirs(test_output_dir, exist_ok=True)
            
            # Save the audio
            timestamp = int(time.time())
            test_file_path = os.path.join(test_output_dir, f"direct_csm_test_{timestamp}.wav")
            direct_csm.save_audio(audio, sample_rate, test_file_path)
            
            # Update task with success
            task_manager.update_task(
                task_id,
                status="completed",
                result={
                    "file_path": test_file_path,
                    "file_url": f"/api/admin/voices/test/direct_csm_test_{timestamp}.wav",
                    "message": "Direct CSM test completed successfully"
                }
            )
            logger.info(f"Direct CSM test completed for task {task_id}: {test_file_path}")
            
        except DirectCSMError as e:
            logger.error(f"Direct CSM test failed: {e}")
            task_manager.update_task(
                task_id,
                status="failed",
                error=f"Direct CSM test failed: {str(e)}"
            )
            
    except Exception as e:
        logger.error(f"Error in direct CSM test: {e}")
        task_manager.update_task(
            task_id,
            status="failed",
            error=f"Error in direct CSM test: {str(e)}"
        )


@router.get("/models/direct-csm-info")
async def get_direct_csm_info(username: str = Depends(verify_credentials)):
    """Get direct CSM information."""
    logger.info(f"Getting direct CSM info for user: {username}")
    
    # Check if direct CSM is enabled in config
    is_enabled = config.USE_DIRECT_CSM
    
    # Check if direct CSM is loaded
    is_loaded = False
    if voice_generator and voice_generator.is_initialized() and voice_generator.direct_csm is not None:
        is_loaded = True
    
    # Get the CSM path
    csm_path = config.DIRECT_CSM_PATH
    
    # Check if the CSM path exists
    path_exists = os.path.exists(csm_path)
    
    # Check if the CSM path has the required files
    has_required_files = False
    if path_exists:
        required_files = ["generator.py", "models.py"]
        existing_files = os.listdir(csm_path)
        has_required_files = all(file in existing_files for file in required_files)
    
    return {
        "enabled": is_enabled,
        "loaded": is_loaded,
        "path": csm_path,
        "path_exists": path_exists,
        "has_required_files": has_required_files,
        "status": "Active" if is_loaded else "Inactive"
    } 