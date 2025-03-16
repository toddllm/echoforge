"""
EchoForge UI Routes

This module defines the web UI routes for the EchoForge application.
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

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
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/generate", response_class=HTMLResponse)
async def generate_page(request: Request):
    """Render the generation page."""
    logger.info("Rendering generation page")
    return templates.TemplateResponse(
        "generate.html", 
        {
            "request": request,
            "default_text": "Hello, this is a test of the voice generation system."
        }
    )


@router.get("/characters", response_class=HTMLResponse)
async def characters_page(request: Request):
    """Render the character showcase page."""
    logger.info("Rendering character showcase page")
    return templates.TemplateResponse(
        "characters.html",
        {
            "request": request,
            "default_theme": "light"
        }
    ) 