#!/usr/bin/env python3
"""
Connect Auth Backend Script for EchoForge

This script prepares the EchoForge backend to work with the new NextJS frontend authentication system.
It creates a JWT validation endpoint and sets up the necessary middleware.

Usage:
    python connect_auth_backend.py

This script is for Stage 3 of the authentication migration plan.
"""

import os
import re
import shutil
from pathlib import Path

# Define paths
BASE_DIR = Path(__file__).parent.parent
AUTH_FILE = BASE_DIR / "app" / "core" / "jwt_auth.py"
MIDDLEWARE_FILE = BASE_DIR / "app" / "core" / "jwt_middleware.py"
MAIN_FILE = BASE_DIR / "app" / "main.py"
API_AUTH_DIR = BASE_DIR / "app" / "api" / "auth" / "jwt"

# Create backup directory
BACKUP_DIR = BASE_DIR / "backups" / "jwt_auth_backup"
os.makedirs(BACKUP_DIR, exist_ok=True)

# Create necessary directories
os.makedirs(API_AUTH_DIR, exist_ok=True)

def backup_file(file_path):
    """Create a backup of the specified file."""
    if file_path.exists():
        backup_path = BACKUP_DIR / file_path.name
        shutil.copy2(file_path, backup_path)
        print(f"Backed up {file_path} to {backup_path}")

def create_jwt_auth_file():
    """Create the JWT authentication module."""
    content = '''
from typing import Dict, Optional, Union
import time
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from app.core.config import get_settings

logger = logging.getLogger("echoforge.core.jwt_auth")

# JWT configuration
settings = get_settings()
JWT_SECRET = settings.JWT_SECRET
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Security scheme for Swagger UI
security = HTTPBearer()

def create_access_token(data: Dict[str, Union[str, int]], expires_delta: Optional[int] = None) -> str:
    """
    Create a new JWT token.
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time in minutes
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    expire = time.time() + (expires_delta or TOKEN_EXPIRE_MINUTES) * 60
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return encoded_jwt

def decode_token(token: str) -> Dict:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token data
    
    Raises:
        HTTPException: If the token is invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        logger.debug(f"Decoded token: {payload}")
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get the current user from JWT token.
    
    Args:
        credentials: HTTP Authorization credentials with the JWT token
        
    Returns:
        User data from the token
        
    Raises:
        HTTPException: If the token is missing or invalid
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    # You can add additional validation here
    # For example, checking if the user still exists in the database
    
    return payload
'''
    
    with open(AUTH_FILE, 'w') as f:
        f.write(content.strip())
    
    print(f"Created JWT authentication module at {AUTH_FILE}")

def create_jwt_middleware_file():
    """Create the JWT middleware file."""
    content = '''
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
from app.core.jwt_auth import decode_token

logger = logging.getLogger("echoforge.core.jwt_middleware")

class JWTMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication."""
    
    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: Optional[list[str]] = None
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or []
        
    async def dispatch(self, request: Request, call_next: Callable):
        """Process the request through the middleware."""
        
        # Skip middleware for excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            logger.debug(f"Skipping JWT middleware for excluded path: {path}")
            return await call_next(request)
        
        # Skip for OPTIONS requests (pre-flight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                # Decode and validate token
                payload = decode_token(token)
                # Attach user data to request state
                request.state.user = payload
                logger.debug(f"User authenticated via JWT: {payload.get('email')}")
            except Exception as e:
                logger.warning(f"JWT validation failed: {str(e)}")
                # Continue without authentication - API routes will handle auth dependency
        
        # Continue with request processing
        return await call_next(request)
'''
    
    with open(MIDDLEWARE_FILE, 'w') as f:
        f.write(content.strip())
    
    print(f"Created JWT middleware at {MIDDLEWARE_FILE}")

def create_jwt_validate_endpoint():
    """Create JWT validation API endpoint."""
    jwt_validate_file = API_AUTH_DIR / "validate.py"
    
    content = '''
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.jwt_auth import get_current_user

router = APIRouter()

@router.post("/validate")
async def validate_token(user_data = Depends(get_current_user)):
    """
    Validate a JWT token and return the user data.
    
    This endpoint is used by the frontend to validate authentication tokens.
    """
    return {
        "status": "success",
        "data": user_data
    }
'''
    
    with open(jwt_validate_file, 'w') as f:
        f.write(content.strip())
    
    # Create __init__.py for the package
    init_file = API_AUTH_DIR / "__init__.py"
    with open(init_file, 'w') as f:
        f.write("from app.api.auth.jwt.validate import router\n")
    
    print(f"Created JWT validate endpoint at {jwt_validate_file}")

def update_main_file():
    """Update the main.py file to include JWT middleware."""
    backup_file(MAIN_FILE)
    
    with open(MAIN_FILE, 'r') as f:
        content = f.read()
    
    # Add import for JWT middleware
    import_statement = "from app.core.jwt_middleware import JWTMiddleware\n"
    content = re.sub(r'import logging\n', f'import logging\n{import_statement}', content)
    
    # Add middleware to the app
    middleware_code = '''
    # Add JWT middleware with excluded paths
    app.add_middleware(
        JWTMiddleware,
        exclude_paths=[
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/auth/jwt/validate",
            "/api/health",
            "/static",
        ]
    )
'''
    content = re.sub(r'app = FastAPI\([^)]*\)\n', f'app = FastAPI()\n{middleware_code}', content)
    
    # Include the JWT auth router
    router_code = 'app.include_router(auth.jwt.router, prefix="/api/auth/jwt", tags=["JWT Auth"])\n'
    content = re.sub(r'# Include routers', f'# Include routers\n{router_code}', content)
    
    with open(MAIN_FILE, 'w') as f:
        f.write(content)
    
    print(f"Updated {MAIN_FILE} to include JWT middleware and routes")

def create_env_changes_file():
    """Create a file with required environment variable changes."""
    env_file = BASE_DIR / "JWT_ENV_CHANGES.md"
    
    content = '''# JWT Authentication Environment Variables

Add the following to your `.env` file or environment:

```
# JWT Configuration
JWT_SECRET=replace-with-same-secret-key-as-frontend
```

Make sure this JWT_SECRET matches the one used in the frontend's .env.local file.
'''
    
    with open(env_file, 'w') as f:
        f.write(content)
    
    print(f"Created environment variable instructions at {env_file}")

def main():
    print("Starting JWT backend connection setup for EchoForge...")
    
    try:
        create_jwt_auth_file()
        create_jwt_middleware_file()
        create_jwt_validate_endpoint()
        update_main_file()
        create_env_changes_file()
        
        print("\nJWT backend connection setup completed successfully.")
        print("Please add JWT_SECRET to your environment variables or .env file.")
        print("See JWT_ENV_CHANGES.md for details.")
        print("\nTo restore original files, copy from:", BACKUP_DIR)
    except Exception as e:
        print(f"Error: {e}")
        print("JWT backend connection setup failed.")

if __name__ == "__main__":
    main() 