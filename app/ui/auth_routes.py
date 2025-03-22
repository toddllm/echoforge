"""
EchoForge Authentication UI Routes

This module defines the web UI routes for authentication pages of the EchoForge application.
"""

import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.core import config
from app.core.security import get_current_user

# Configure logging
logger = logging.getLogger("echoforge.ui.auth")

# Create router
router = APIRouter(tags=["auth_ui"])

# Set up Jinja2 templates
templates_dir = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=templates_dir)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page."""
    logger.info("Rendering login page")
    return templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "default_theme": config.DEFAULT_THEME
        }
    )


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Render the signup page."""
    logger.info("Rendering signup page")
    return templates.TemplateResponse(
        "auth/signup.html",
        {
            "request": request,
            "default_theme": config.DEFAULT_THEME
        }
    )


@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Render the forgot password page."""
    logger.info("Rendering forgot password page")
    return templates.TemplateResponse(
        "auth/forgot_password.html",
        {
            "request": request,
            "default_theme": config.DEFAULT_THEME
        }
    )


@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request):
    """Render the reset password page."""
    logger.info("Rendering reset password page")
    return templates.TemplateResponse(
        "auth/reset_password.html",
        {
            "request": request,
            "default_theme": config.DEFAULT_THEME
        }
    )


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Render the user profile page."""
    logger.info("Rendering profile page")
    return templates.TemplateResponse(
        "auth/profile.html",
        {
            "request": request,
            "default_theme": config.DEFAULT_THEME
        }
    )
