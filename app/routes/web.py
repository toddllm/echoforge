from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import time
import os
from pathlib import Path

router = APIRouter()

# Get templates directory
templates_dir = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Index page."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "page_title": "EchoForge - Voice Generation",
            "default_theme": "light",
            "current_time": int(time.time())
        }
    )

@router.get("/characters", response_class=HTMLResponse)
async def characters_page(request: Request):
    """Character showcase page."""
    return templates.TemplateResponse(
        "character_showcase.html",
        {
            "request": request,
            "page_title": "EchoForge - Character Showcase",
            "default_theme": "light",
            "current_time": int(time.time())
        }
    )

@router.get("/debug", response_class=HTMLResponse)
async def debug_generate_page(request: Request):
    """Debug page for voice generation."""
    return templates.TemplateResponse(
        "debug_generate.html",
        {
            "request": request,
            "page_title": "EchoForge - Debug Voice Generation",
            "default_theme": "light",
            "current_time": int(time.time())
        }
    ) 