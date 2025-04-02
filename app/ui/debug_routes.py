"""
Debug routes for EchoForge - Only enabled in development mode.
These routes help with debugging and will be disabled in production.
"""

import logging
import json
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.core.auth import get_current_username
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.db.models import UserProfile

# Configure logging
logger = logging.getLogger("echoforge.debug")

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/session")
async def debug_session(request: Request, username: str = Depends(get_current_username)):
    """
    Debug endpoint to view current session state.
    Only available in development mode.
    """
    # Only allow access to authenticated users
    if username == "anonymous":
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Check if we're in development mode
    if not request.app.debug:
        raise HTTPException(status_code=403, detail="Debug endpoints only available in development mode")
    
    # Get session data
    session = getattr(request.state, "session", None)
    if not session:
        return JSONResponse({"error": "No session found"})
    
    # Extract relevant session details while maintaining security
    session_data = {
        "is_authenticated": getattr(session, "is_authenticated", False),
        "user_id": getattr(session, "user_id", None),
        "data": getattr(session, "data", {}),
        "session_id": getattr(session, "session_id", None)
    }
    
    # Log for debugging
    logger.info(f"Session debug requested by {username}: {json.dumps(session_data)}")
    
    return JSONResponse(session_data)

@router.get("/profile")
async def debug_profile(
    request: Request, 
    username: str = Depends(get_current_username),
    db: Session = Depends(get_db)
):
    """
    Debug endpoint to view current profile data from the database.
    Only available in development mode.
    """
    # Only allow access to authenticated users
    if username == "anonymous":
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Check if we're in development mode
    if not request.app.debug:
        raise HTTPException(status_code=403, detail="Debug endpoints only available in development mode")
    
    # Get user ID from session
    session = getattr(request.state, "session", None)
    user_id = getattr(session, "user_id", None)
    
    if not user_id:
        return JSONResponse({"error": "No user ID in session"})
    
    # Query the database for the user profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    if not profile:
        return JSONResponse({"error": "Profile not found"})
    
    # Extract profile data
    profile_data = {
        "user_id": profile.user_id,
        "theme_preference": profile.theme_preference,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "bio": profile.bio,
        "created_at": str(profile.created_at),
        "updated_at": str(profile.updated_at) if profile.updated_at else None
    }
    
    return JSONResponse(profile_data)
