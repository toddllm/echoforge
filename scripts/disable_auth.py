#!/usr/bin/env python3
"""
Disable Authentication Script for EchoForge

This script modifies the necessary files to disable the authentication system
in EchoForge for Stage 1 of the authentication migration plan.

Usage:
    python disable_auth.py

This will:
1. Modify auth.py to bypass authentication checks
2. Update middleware to skip authentication
3. Disable authentication routes
"""

import os
import re
import shutil
from pathlib import Path

# Define paths
BASE_DIR = Path(__file__).parent.parent
AUTH_FILE = BASE_DIR / "app" / "core" / "auth.py"
MIDDLEWARE_FILE = BASE_DIR / "app" / "core" / "session_middleware.py"
ROUTES_FILE = BASE_DIR / "app" / "ui" / "routes.py"

# Create backup directory
BACKUP_DIR = BASE_DIR / "backups" / "auth_backup"
os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_file(file_path):
    """Create a backup of the specified file."""
    backup_path = BACKUP_DIR / file_path.name
    shutil.copy2(file_path, backup_path)
    print(f"Backed up {file_path} to {backup_path}")

def modify_auth_file():
    """Modify auth.py to bypass authentication checks."""
    backup_file(AUTH_FILE)
    
    with open(AUTH_FILE, 'r') as f:
        content = f.read()
    
    # Add bypass to verify_credentials function
    modified_content = re.sub(
        r'def verify_credentials\(credentials: HTTPBasicCredentials\):',
        'def verify_credentials(credentials: HTTPBasicCredentials):\n    # AUTH DISABLED FOR MIGRATION\n    return True\n    # Original code below',
        content
    )
    
    # Add bypass to auth_required dependency
    modified_content = re.sub(
        r'def auth_required\(request: Request\):',
        'def auth_required(request: Request):\n    # AUTH DISABLED FOR MIGRATION\n    return lambda: None\n    # Original code below',
        modified_content
    )
    
    with open(AUTH_FILE, 'w') as f:
        f.write(modified_content)
    
    print(f"Modified {AUTH_FILE} to bypass authentication")

def modify_middleware_file():
    """Modify session middleware to skip authentication checks."""
    backup_file(MIDDLEWARE_FILE)
    
    with open(MIDDLEWARE_FILE, 'r') as f:
        content = f.read()
    
    # Modify _handle_request method to skip auth checks
    modified_content = re.sub(
        r'async def _handle_request\(self, request: Request, call_next\)',
        'async def _handle_request(self, request: Request, call_next)\n        # AUTH DISABLED FOR MIGRATION\n        session = Session("disabled-auth-session")\n        session.is_authenticated = True\n        request.state.session = session\n        return await call_next(request)\n        # Original code below',
        content
    )
    
    with open(MIDDLEWARE_FILE, 'w') as f:
        f.write(modified_content)
    
    print(f"Modified {MIDDLEWARE_FILE} to bypass session checks")

def modify_routes_file():
    """Disable authentication in UI routes."""
    backup_file(ROUTES_FILE)
    
    with open(ROUTES_FILE, 'r') as f:
        content = f.read()
    
    # Find login related route handlers and add bypass
    patterns = [
        r'@router.get\("/login"\)',
        r'@router.post\("/login"\)',
        r'@router.get\("/signup"\)',
        r'@router.post\("/signup"\)',
        r'@router.get\("/forgot-password"\)',
        r'@router.post\("/forgot-password"\)',
        r'@router.get\("/reset-password"\)'
    ]
    
    modified_content = content
    for pattern in patterns:
        modified_content = re.sub(
            pattern + r'([^@]+)',
            pattern + r'\n' + 'async def disabled_auth_route(request: Request):\n    # AUTH DISABLED FOR MIGRATION\n    return RedirectResponse(url="/", status_code=302)\n\n',
            modified_content
        )
    
    with open(ROUTES_FILE, 'w') as f:
        f.write(modified_content)
    
    print(f"Modified {ROUTES_FILE} to disable auth routes")

def main():
    print("Starting authentication disablement for EchoForge...")
    
    try:
        modify_auth_file()
        modify_middleware_file()
        modify_routes_file()
        
        print("\nAuthentication has been successfully disabled.")
        print("Please restart the EchoForge server to apply changes.")
        print("To restore original files, copy from:", BACKUP_DIR)
    except Exception as e:
        print(f"Error: {e}")
        print("Authentication disablement failed.")

if __name__ == "__main__":
    main() 