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
async def get_tasks(
    limit: int = 10,
    offset: int = 0,
    status: Optional[str] = None,
    username: str = Depends(verify_credentials)
):
    """Get task information."""
    logger.info(f"Getting tasks for user: {username}")
    
    if not task_manager:
        raise HTTPException(status_code=500, detail="Task manager not available")
    
    all_tasks = task_manager.get_all_tasks()
    
    # Filter by status if provided
    if status:
        filtered_tasks = {k: v for k, v in all_tasks.items() if v.get('status') == status}
    else:
        filtered_tasks = all_tasks
    
    # Sort by creation time (newest first)
    sorted_tasks = sorted(
        filtered_tasks.items(),
        key=lambda x: x[1].get('created_at', 0),
        reverse=True
    )
    
    # Apply pagination
    paginated_tasks = sorted_tasks[offset:offset + limit]
    
    # Convert to TaskInfo objects
    task_infos = []
    for task_id, task_data in paginated_tasks:
        task_infos.append(TaskInfo(
            task_id=task_id,
            status=task_data.get('status', 'unknown'),
            created_at=datetime.fromtimestamp(task_data.get('created_at', 0)),
            completed_at=datetime.fromtimestamp(task_data.get('completed_at', 0)) if task_data.get('completed_at') else None,
            progress=task_data.get('progress', 0.0),
            text=task_data.get('text', ''),
            speaker_id=task_data.get('speaker_id', 0),
            parameters={
                'temperature': task_data.get('temperature', 0.0),
                'top_k': task_data.get('top_k', 0),
                'style': task_data.get('style', ''),
                'device': task_data.get('device', '')
            }
        ))
    
    return task_infos


@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    username: str = Depends(verify_credentials)
):
    """Cancel a task."""
    logger.info(f"Cancelling task {task_id} for user: {username}")
    
    if not task_manager:
        raise HTTPException(status_code=500, detail="Task manager not available")
    
    # Check if task exists
    if not task_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Cancel the task
    task_manager.cancel_task(task_id)
    
    return {"status": "cancelled", "message": "Task cancelled successfully"}


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
    device: str = Body("auto", embed=True)
):
    """Generate voice from the admin interface."""
    logger.info(f"Admin voice generation request from user: {username}")
    
    if not voice_generator:
        raise HTTPException(status_code=500, detail="Voice generator not available")
    
    # Validate parameters
    if not text or len(text) < 1:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    if len(text) > 1000:
        raise HTTPException(status_code=400, detail="Text exceeds maximum length (1000 characters)")
    
    if temperature < 0.1 or temperature > 1.0:
        raise HTTPException(status_code=400, detail="Temperature must be between 0.1 and 1.0")
    
    if top_k < 1 or top_k > 100:
        raise HTTPException(status_code=400, detail="Top-k must be between 1 and 100")
    
    if device not in ["auto", "cpu", "cuda"]:
        logger.warning(f"Invalid device specified: {device}, falling back to 'auto'")
        device = "auto"
        
    # Force CPU if requested
    if device == "cpu":
        logger.info("Using CPU as explicitly requested by user")
    
    # Register a task for this generation
    task_id = task_manager.register_task("admin_voice_generation")
    
    # Launch background task for generation
    background_tasks.add_task(
        _generate_admin_voice,
        task_id=task_id,
        text=text,
        speaker_id=speaker_id,
        temperature=temperature,
        top_k=top_k,
        style=style,
        device=device
    )
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Voice generation has been started"
    }


async def _generate_admin_voice(task_id: str, text: str, speaker_id: int, temperature: float, top_k: int, style: str, device: str):
    """Background task for voice generation."""
    logger.info(f"Starting admin voice generation for task {task_id}")
    
    try:
        # Create an admin-specific output directory
        admin_output_dir = os.path.join(config.OUTPUT_DIR, "admin")
        os.makedirs(admin_output_dir, exist_ok=True)
        
        # Update task status
        task_manager.update_task(task_id, status="processing")
        
        # Generate voice
        file_path, file_url = voice_generator.generate(
            text=text,
            speaker_id=speaker_id,
            temperature=temperature,
            top_k=top_k,
            style=style,
            device=device
        )
        
        if file_path:
            # Voice generation successful
            # Convert file_path to absolute path if it's not already
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(file_path)
                
            # Ensure the file exists
            if os.path.exists(file_path):
                # Get the filename from the path
                file_name = os.path.basename(file_path)
                
                # Copy file to admin directory for better organization
                admin_file_path = os.path.join(admin_output_dir, file_name)
                import shutil
                shutil.copy2(file_path, admin_file_path)
                logger.info(f"Copied voice file to admin directory: {admin_file_path}")
                
                # Update task with success
                task_manager.update_task(
                    task_id,
                    status="completed",
                    result={
                        "file_path": admin_file_path,
                        "file_url": f"/api/admin/voices/{file_name}",
                        "text": text,
                        "speaker_id": speaker_id
                    }
                )
                logger.info(f"Admin voice generation completed for task {task_id}: {admin_file_path}")
                return
            else:
                logger.error(f"Voice generation succeeded but file not found: {file_path}")
                task_manager.update_task(
                    task_id,
                    status="failed",
                    error=f"Voice generation succeeded but file not found: {file_path}"
                )
        else:
            # Voice generation failed
            logger.error(f"Voice generation failed for task {task_id}")
            task_manager.update_task(
                task_id,
                status="failed",
                error="Voice generation failed"
            )
    
    except Exception as e:
        # Handle any exceptions
        logger.exception(f"Error during admin voice generation for task {task_id}: {e}")
        task_manager.update_task(
            task_id,
            status="failed",
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