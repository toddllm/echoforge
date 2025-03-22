"""
Security utilities for EchoForge authentication system.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token settings
SECRET_KEY = os.environ.get("SECRET_KEY", "CHANGEME_THIS_IS_NOT_SECURE_FOR_PRODUCTION")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# OAuth2 password bearer for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def generate_reset_token() -> str:
    """Generate a password reset token."""
    return uuid.uuid4().hex

def validate_redirect_url(url: Optional[str], allowed_hosts: Optional[list] = None) -> Optional[str]:
    """Validate and sanitize a redirect URL to prevent open redirect vulnerabilities.
    
    Args:
        url: The redirect URL to validate
        allowed_hosts: List of allowed external hosts for redirects (if None, only relative URLs allowed)
        
    Returns:
        The validated URL if safe, or None if unsafe
    """
    if url is None or not url.strip():
        return None
    
    # Clean up the URL
    url = url.strip()
    
    # Relative URLs are always safe
    if url.startswith('/') and not url.startswith('//'):
        return url
    
    # Check if this appears to be an absolute URL
    if '://' in url:
        # Only allow specific protocols
        if not (url.startswith('http://') or url.startswith('https://')):
            return None
            
        # If we have allowed hosts, check against them
        if allowed_hosts:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            hostname = parsed.netloc
            
            # Check if the hostname is in our allowed list
            if hostname in allowed_hosts:
                return url
            
            return None
        else:
            # If no allowed hosts specified, only allow relative URLs
            return None
    
    # Unknown URL format, reject it
    return None

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

def is_admin(user: User = Depends(get_current_user)) -> bool:
    """Check if user is an admin."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return True
