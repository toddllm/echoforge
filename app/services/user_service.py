"""
User service for EchoForge.
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, constr

from app.db.models import User, UserProfile
from app.core.security import get_password_hash, verify_password, generate_reset_token

logger = logging.getLogger(__name__)

# Pydantic models for request validation
class UserCreate(BaseModel):
    email: EmailStr
    username: constr(min_length=3, max_length=50)
    password: constr(min_length=8)
    first_name: constr(min_length=1)
    last_name: constr(min_length=1)
    
class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    organization: Optional[str] = None
    theme_preference: Optional[str] = None

class UserPasswordReset(BaseModel):
    token: str
    new_password: constr(min_length=8)

class UserPasswordChange(BaseModel):
    current_password: str
    new_password: constr(min_length=8)

class UserForgotPassword(BaseModel):
    email: EmailStr

# Response models
class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    first_name: str
    last_name: str
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    first_name: str
    last_name: str
    bio: Optional[str] = None
    organization: Optional[str] = None
    theme_preference: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# User service functions
def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user."""
    # Check if user already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create user with hashed password
    user_id = str(uuid.uuid4())
    db_user = User(
        id=user_id,
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        is_active=True,
        is_admin=False
    )
    
    # Create user profile
    db_profile = UserProfile(
        id=str(uuid.uuid4()),
        user_id=user_id,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    
    try:
        db.add(db_user)
        db.add(db_profile)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user by username/email and password."""
    # Try to find user by username or email
    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user

def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email."""
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get a user by username."""
    return db.query(User).filter(User.username == username).first()

def update_user_profile(db: Session, user_id: str, profile_data: UserUpdate) -> Optional[UserProfile]:
    """Update a user's profile."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    if not profile:
        return None
    
    # Update only provided fields
    update_data = profile_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    try:
        db.commit()
        db.refresh(profile)
        return profile
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )

def change_user_password(db: Session, user_id: str, current_password: str, new_password: str) -> bool:
    """Change a user's password."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return False
    
    # Verify current password
    if not verify_password(current_password, user.hashed_password):
        return False
    
    # Update password
    user.hashed_password = get_password_hash(new_password)
    
    try:
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error changing password: {e}")
        return False

def create_password_reset(db: Session, email: str) -> Optional[Dict[str, str]]:
    """Create a password reset token."""
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return None
    
    # Generate reset token
    reset_token = generate_reset_token()
    reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    
    # Update user with reset token
    user.reset_token = reset_token
    user.reset_token_expires = reset_token_expires
    
    try:
        db.commit()
        return {
            "user_id": user.id,
            "token": reset_token,
            "expires": reset_token_expires
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating password reset: {e}")
        return None

def verify_reset_token(db: Session, token: str) -> Optional[User]:
    """Verify a password reset token."""
    user = db.query(User).filter(User.reset_token == token).first()
    
    if not user:
        return None
    
    # Check if token is expired
    if user.reset_token_expires and user.reset_token_expires < datetime.utcnow():
        return None
    
    return user

def reset_password_with_token(db: Session, token: str, new_password: str) -> bool:
    """Reset a user's password using a reset token."""
    user = verify_reset_token(db, token)
    
    if not user:
        return False
    
    # Update password and clear reset token
    user.hashed_password = get_password_hash(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    
    try:
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error resetting password: {e}")
        return False
