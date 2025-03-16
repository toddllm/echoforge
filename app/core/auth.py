"""
Authentication module for EchoForge.

This module provides authentication functionality for securing the application.
"""

import secrets
import logging
import os
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core import config

# Setup logging
logger = logging.getLogger(__name__)

# Initialize HTTP Basic Auth
security = HTTPBasic()


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify HTTP Basic Auth credentials."""
    # Skip verification in test mode
    if os.environ.get("ECHOFORGE_TEST") == "true":
        logger.info("Test mode - bypassing credential verification")
        return "test_user"
        
    correct_username = secrets.compare_digest(credentials.username, config.AUTH_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, config.AUTH_PASSWORD)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def auth_required(request: Request):
    """
    Determines if authentication is required based on configuration settings.
    
    Authentication is required if:
    1. ENABLE_AUTH is True, or
    2. ALLOW_PUBLIC_SERVING is True, AUTH_REQUIRED_FOR_PUBLIC is True, and 
       the host is set to PUBLIC_HOST
       
    Authentication is bypassed in test mode.
    """
    # Skip auth in test mode
    if os.environ.get("ECHOFORGE_TEST") == "true":
        logger.debug("Test mode - bypassing authentication requirement")
        return None
        
    # Check if we're in public serving mode with auth required
    app = request.app
    host = getattr(app, 'host', config.DEFAULT_HOST)
    
    is_public_serving = (
        config.ALLOW_PUBLIC_SERVING and 
        config.AUTH_REQUIRED_FOR_PUBLIC and
        host == config.PUBLIC_HOST
    )
    
    # If general auth is enabled or we're in public serving mode with auth required
    if config.ENABLE_AUTH or is_public_serving:
        # This will trigger the auth flow
        return Depends(verify_credentials)
    
    # No auth required, return a no-op dependency
    return None 