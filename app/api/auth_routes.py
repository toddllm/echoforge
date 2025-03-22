"""
Authentication API Routes

This module defines the API routes for authentication.
"""

import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, Form, Request, status
from fastapi.responses import JSONResponse, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
import secrets
import os

from app.db.models import User, UserProfile
from app.db.session import get_db
from app.core.security import get_password_hash
from sqlalchemy.orm import Session

from app.core import config

# Configure logging
logger = logging.getLogger("echoforge.api.auth")

# Create router
router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):
    """Login endpoint for form-based authentication."""
    logger.info(f"Login attempt for user: {form_data.username}")
    
    # Skip verification in test mode
    if os.environ.get("ECHOFORGE_TEST") == "true":
        logger.info("Test mode - bypassing credential verification")
        token = "dummy_token_" + secrets.token_hex(16)

    # Create response with token
    response = JSONResponse(content={
        "access_token": token,
        "token_type": "bearer",
        "username": form_data.username,
        "is_admin": True
    })
    
    # Set session cookie
    response.set_cookie(
        key="echoforge_session",
        value="session_" + secrets.token_hex(16),
        httponly=True,
        max_age=86400,  # 24 hours
        secure=False  # Set to True in production with HTTPS
    )
    
    return response
    
    # Verify credentials against config
    correct_username = secrets.compare_digest(form_data.username, config.AUTH_USERNAME)
    correct_password = secrets.compare_digest(form_data.password, config.AUTH_PASSWORD)
    
    if not (correct_username and correct_password):
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    
    # In a real application, you would:
    # 1. Generate a JWT token
    # 2. Store user session information
    # For simplicity, we're just returning a dummy token
    
    logger.info(f"Successful login for user: {form_data.username}")
    token = "dummy_token_" + secrets.token_hex(16)

    # Create response with token
    response = JSONResponse(content={
        "access_token": token,
        "token_type": "bearer",
        "username": form_data.username,
        "is_admin": True
    })
    
    # Set session cookie
    response.set_cookie(
        key="echoforge_session",
        value="session_" + secrets.token_hex(16),
        httponly=True,
        max_age=86400,  # 24 hours
        secure=False  # Set to True in production with HTTPS
    )
    
    return response

@router.post("/logout")
async def logout():
    """Logout endpoint."""
    return {"message": "Logged out successfully"}


class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    first_name: str
    last_name: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    is_admin: bool
    first_name: str
    last_name: str


@router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a new user account."""
    logger.info(f"Signup attempt for user: {user_data.username}")
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        logger.warning(f"Signup failed: Email already exists: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        logger.warning(f"Signup failed: Username already exists: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create user
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        id=user_id,
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False
    )
    
    # Create user profile
    profile_id = str(uuid.uuid4())
    new_profile = UserProfile(
        id=profile_id,
        user_id=user_id,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    
    # Save both to database
    db.add(new_user)
    db.add(new_profile)
    db.commit()
    db.refresh(new_user)
    db.refresh(new_profile)
    
    logger.info(f"User created successfully: {user_data.username}")
    
    # Return user data with profile info
    return {
        "id": new_user.id,
        "email": new_user.email,
        "username": new_user.username,
        "is_active": new_user.is_active,
        "is_admin": new_user.is_admin,
        "first_name": new_profile.first_name,
        "last_name": new_profile.last_name
    }
