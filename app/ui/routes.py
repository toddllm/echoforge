"""
EchoForge UI Routes

This module defines the web UI routes for the EchoForge application.
"""

import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import torch

from app.core import config
from app.core.auth import verify_credentials, auth_required

# Configure logging
logger = logging.getLogger("echoforge.ui")

# Create router
router = APIRouter(tags=["ui"])

# Set up Jinja2 templates
templates_dir = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=templates_dir)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the home page."""
    logger.info("Rendering home page")
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "default_theme": config.DEFAULT_THEME
        }
    )


@router.get("/generate", response_class=HTMLResponse)
async def generate_page(request: Request):
    """Render the generation page."""
    logger.info("Rendering generation page")
    return templates.TemplateResponse(
        "generate.html", 
        {
            "request": request,
            "default_text": "Hello, this is a test of the voice generation system.",
            "default_theme": config.DEFAULT_THEME
        }
    )


@router.get("/characters", response_class=HTMLResponse)
async def characters_page(request: Request):
    """Render the character showcase page."""
    logger.info("Rendering character showcase page")
    # Serve the static HTML file directly
    from fastapi.responses import FileResponse
    return FileResponse("/home/tdeshane/echoforge/app/static/character_showcase.html")


@router.get("/test", response_class=HTMLResponse)
async def test_page(request: Request):
    """Render the test page for verifying functionality."""
    logger.info("Rendering test page")
    # Serve the static HTML file directly
    from fastapi.responses import FileResponse
    return FileResponse("/home/tdeshane/echoforge/app/static/test_page.html")

# Admin routes
@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, username: str = Depends(verify_credentials)):
    """Render the admin dashboard page."""
    logger.info(f"Rendering admin dashboard for user: {username}")
    
    # Get system stats (mock data for now)
    system_stats = {
        "model_status": "Loaded",
        "active_tasks": 0,
        "voices_count": 10,
        "cpu_usage": 25,
        "memory_usage": 40,
        "gpu_usage": 15,
        "disk_usage": 30,
        "recent_generations": 150
    }
    
    # Mock chart data
    chart_data = {
        "generation": {
            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "data": [65, 59, 80, 81, 56, 55]
        },
        "usage": {
            "labels": ["CPU", "Memory", "Disk", "Network"],
            "data": [25, 40, 30, 15]
        },
        "performance": {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "data": [10, 15, 20, 25, 30, 20, 15],
            "cpu": [15, 20, 25, 30, 35, 25, 20],
            "memory": [25, 30, 35, 40, 30, 25, 20],
            "disk": [10, 15, 20, 15, 10, 15, 10],
            "response_time": [150, 120, 130, 140, 110, 125, 135]
        }
    }
    
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "default_theme": config.DEFAULT_THEME,
            "current_user": {"name": username},
            "system_stats": system_stats,
            "system_metrics": system_stats,
            "system_status": "ok",
            "version": config.APP_VERSION,
            "notifications_count": 0,
            "messages": [],
            "chart_data": chart_data
        }
    )

@router.get("/admin/models", response_class=HTMLResponse)
async def admin_models(request: Request, username: str = Depends(verify_credentials)):
    """Render the admin models page."""
    logger.info(f"Rendering admin models page for user: {username}")
    
    # Mock model data - replace with actual data in production
    active_model = {
        "name": "CSM-1B",
        "description": "Character Speech Model (1B parameters)",
        "status": "active",
        "version": "1.0.0",
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "loaded_at": "2023-06-15 08:30:45",
        "memory_usage": "1.2 GB"
    }
    
    model_info = [
        {
            "id": "csm-1b",
            "name": "CSM-1B",
            "description": "Character Speech Model with 1B parameters",
            "type": "csm",
            "status": "active",
            "version": "1.0.0",
            "parameters": "1B",
            "last_update": "2023-06-15",
            "size": "1.2 GB"
        },
        {
            "id": "csm-medium",
            "name": "CSM-Medium",
            "description": "Medium-sized Character Speech Model",
            "type": "csm",
            "status": "inactive",
            "version": "0.9.5",
            "parameters": "350M",
            "last_update": "2023-05-20",
            "size": "450 MB"
        },
        {
            "id": "embeddings-v1",
            "name": "Voice Embeddings v1",
            "description": "Voice embeddings model for voice cloning",
            "type": "embeddings",
            "status": "inactive",
            "version": "1.0.0",
            "parameters": "250M",
            "last_update": "2023-06-10",
            "size": "320 MB"
        }
    ]
    
    # Setup pagination information
    per_page = 10  # Default number of items per page
    total_items = len(model_info)
    current_page = 1
    total_pages = max(1, (total_items + per_page - 1) // per_page)  # Ceiling division
    
    start_idx = (current_page - 1) * per_page
    end_idx = min(start_idx + per_page, total_items)
    
    pagination = {
        "total": total_items,
        "per_page": per_page,
        "current": current_page,
        "start": start_idx + 1 if total_items > 0 else 0,
        "end": end_idx,
        "has_prev": current_page > 1,
        "has_next": current_page < total_pages,
        "pages": list(range(1, total_pages + 1))
    }
    
    return templates.TemplateResponse(
        "admin/models.html",
        {
            "request": request,
            "default_theme": config.DEFAULT_THEME,
            "current_user": {"name": username},
            "system_status": "ok",
            "version": config.APP_VERSION,
            "notifications_count": 0,
            "messages": [],
            "active_model": active_model,
            "model_info": model_info,
            "pagination": pagination
        }
    )

@router.get("/admin/voices", response_class=HTMLResponse)
async def admin_voices(request: Request, username: str = Depends(verify_credentials)):
    """Render the admin voices page."""
    logger.info(f"Rendering admin voices page for user: {username}")
    
    # Mock voice stats data - replace with actual data in production
    voice_stats = {
        "total": 8,
        "male": 3,
        "female": 4,
        "child": 1
    }
    
    # Mock model info - replace with actual data in production
    model_info = {
        "name": "CSM-1B",
        "version": "1.0.0",
        "loaded": True,
        "type": "neural_tts"
    }
    
    # Mock voices data - replace with actual data in production
    voices = [
        {
            "id": "voice-1",
            "name": "Male Voice",
            "gender": "male",
            "style": "neutral",
            "created_at": "2023-06-10",
            "status": "active"
        },
        {
            "id": "voice-2",
            "name": "Female Voice",
            "gender": "female",
            "style": "calm",
            "created_at": "2023-06-11",
            "status": "active"
        },
        {
            "id": "voice-3",
            "name": "Child Voice",
            "gender": "neutral",
            "style": "excited",
            "created_at": "2023-06-12",
            "status": "active"
        }
    ]
    
    # Setup pagination information
    per_page = 10  # Default number of items per page
    total_items = len(voices)
    current_page = 1
    total_pages = max(1, (total_items + per_page - 1) // per_page)  # Ceiling division
    
    start_idx = (current_page - 1) * per_page
    end_idx = min(start_idx + per_page, total_items)
    
    pagination = {
        "total": total_items,
        "per_page": per_page,
        "current": current_page,
        "start": start_idx + 1 if total_items > 0 else 0,
        "end": end_idx,
        "has_prev": current_page > 1,
        "has_next": current_page < total_pages,
        "pages": list(range(1, total_pages + 1))
    }
    
    return templates.TemplateResponse(
        "admin/voices.html",
        {
            "request": request,
            "default_theme": config.DEFAULT_THEME,
            "current_user": {"name": username},
            "system_status": "ok",
            "version": config.APP_VERSION,
            "notifications_count": 0,
            "messages": [],
            "voice_stats": voice_stats,
            "model_info": model_info,
            "voices": voices,
            "pagination": pagination
        }
    )

@router.get("/admin/tasks", response_class=HTMLResponse)
async def admin_tasks(request: Request, username: str = Depends(verify_credentials)):
    """Render the admin tasks page."""
    logger.info(f"Rendering admin tasks page for user: {username}")
    
    # Mock task stats data - replace with actual data in production
    task_stats = {
        "total": 15,
        "running": 2,
        "completed": 10,
        "failed": 2,
        "pending": 1
    }
    
    # Mock tasks data - replace with actual data in production
    tasks = [
        {
            "id": "task-001",
            "type": "voice_generation",
            "status": "completed",
            "created_at": "2023-06-15 10:30:45",
            "updated_at": "2023-06-15 10:31:20",
            "text": "Hello, this is a test voice generation.",
            "duration": "35s"
        },
        {
            "id": "task-002",
            "type": "model_loading",
            "status": "completed",
            "created_at": "2023-06-15 09:15:30",
            "updated_at": "2023-06-15 09:16:45",
            "model": "CSM-1B",
            "duration": "1m 15s"
        },
        {
            "id": "task-003",
            "type": "voice_generation",
            "status": "running",
            "created_at": "2023-06-15 10:45:00",
            "updated_at": "2023-06-15 10:45:00",
            "text": "This is a longer text that is currently being processed...",
            "duration": "ongoing"
        }
    ]
    
    # Setup pagination information
    per_page = 10  # Default number of items per page
    total_items = len(tasks)
    current_page = 1
    total_pages = max(1, (total_items + per_page - 1) // per_page)  # Ceiling division
    
    start_idx = (current_page - 1) * per_page
    end_idx = min(start_idx + per_page, total_items)
    
    pagination = {
        "total": total_items,
        "per_page": per_page,
        "current": current_page,
        "start": start_idx + 1 if total_items > 0 else 0,
        "end": end_idx,
        "has_prev": current_page > 1,
        "has_next": current_page < total_pages,
        "pages": list(range(1, total_pages + 1))
    }
    
    return templates.TemplateResponse(
        "admin/tasks.html",
        {
            "request": request,
            "default_theme": config.DEFAULT_THEME,
            "current_user": {"name": username},
            "system_status": "ok",
            "version": config.APP_VERSION,
            "notifications_count": 0,
            "messages": [],
            "task_stats": task_stats,
            "tasks": tasks,
            "pagination": pagination
        }
    )

@router.get("/admin/config", response_class=HTMLResponse)
async def admin_config(request: Request, username: str = Depends(verify_credentials)):
    """Render the admin config page."""
    logger.info(f"Rendering admin config page for user: {username}")
    
    # Create a config object for the template
    config_values = {
        "APP_NAME": config.APP_NAME,
        "APP_DESCRIPTION": "EchoForge - Advanced Voice Synthesis System",
        "DEFAULT_THEME": config.DEFAULT_THEME,
        "DEBUG_MODE": config.DEBUG,
        "LOG_LEVEL": "INFO",
        "OUTPUT_DIR": config.OUTPUT_DIR,
        "MODEL_PATH": config.MODEL_PATH,
        "MAX_TASKS": config.MAX_TASKS,
        "DEFAULT_SPEAKER_ID": config.DEFAULT_SPEAKER_ID,
        "DEFAULT_TEMPERATURE": config.DEFAULT_TEMPERATURE,
        "DEFAULT_TOP_K": config.DEFAULT_TOP_K,
        "DEFAULT_STYLE": config.DEFAULT_STYLE,
        "DEFAULT_DEVICE": config.DEFAULT_DEVICE,
        "SERVER_HOST": "0.0.0.0",
        "SERVER_PORT": 8000,
        "ALLOWED_ORIGINS": "*",
        "AUTH_ENABLED": True,
        "SESSION_TIMEOUT": 3600
    }
    
    return templates.TemplateResponse(
        "admin/config.html",
        {
            "request": request,
            "default_theme": config.DEFAULT_THEME,
            "current_user": {"name": username},
            "system_status": "ok",
            "version": config.APP_VERSION,
            "notifications_count": 0,
            "messages": [],
            "config": config_values
        }
    )

@router.get("/admin/logs", response_class=HTMLResponse)
async def admin_logs(request: Request, username: str = Depends(verify_credentials)):
    """Render the admin logs page."""
    logger.info(f"Rendering admin logs page for user: {username}")
    
    # Mock log sources
    log_sources = [
        "app.core",
        "app.api",
        "app.ui",
        "app.models",
        "voice_generator",
        "task_manager",
        "server"
    ]
    
    # Mock logs data
    logs = [
        {
            "id": "log1",
            "timestamp": "2023-06-15 12:30:45",
            "level": "INFO",
            "source": "app.core",
            "message": "Application started successfully"
        },
        {
            "id": "log2",
            "timestamp": "2023-06-15 12:31:20",
            "level": "INFO",
            "source": "voice_generator",
            "message": "Model loaded successfully on device: CPU"
        },
        {
            "id": "log3",
            "timestamp": "2023-06-15 12:35:12",
            "level": "WARNING",
            "source": "app.api",
            "message": "Rate limit exceeded for user: test_user"
        },
        {
            "id": "log4",
            "timestamp": "2023-06-15 12:40:45",
            "level": "ERROR",
            "source": "task_manager",
            "message": "Failed to process task: task-123 - Out of memory"
        },
        {
            "id": "log5",
            "timestamp": "2023-06-15 12:45:30",
            "level": "INFO",
            "source": "voice_generator",
            "message": "Generated voice for text: 'Hello world'"
        }
    ]
    
    # Setup pagination information
    per_page = 10  # Default number of items per page
    total_items = len(logs)
    current_page = 1
    total_pages = max(1, (total_items + per_page - 1) // per_page)  # Ceiling division
    
    start_idx = (current_page - 1) * per_page
    end_idx = min(start_idx + per_page, total_items)
    
    pagination = {
        "total": total_items,
        "page_size": per_page,  # Different name in the logs template
        "current": current_page,
        "start": start_idx + 1 if total_items > 0 else 0,
        "end": end_idx,
        "has_prev": current_page > 1,
        "has_next": current_page < total_pages,
        "pages": list(range(1, total_pages + 1))
    }
    
    return templates.TemplateResponse(
        "admin/logs.html",
        {
            "request": request,
            "default_theme": config.DEFAULT_THEME,
            "current_user": {"name": username},
            "system_status": "ok",
            "version": config.APP_VERSION,
            "notifications_count": 0,
            "messages": [],
            "log_sources": log_sources,
            "logs": logs,
            "pagination": pagination
        }
    ) 