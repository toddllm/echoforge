#!/usr/bin/env python
"""
Fix authentication session handling in EchoForge
"""
import os
import logging
from pathlib import Path
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def fix_auth_middleware():
    """Fix the auth middleware to properly handle sessions."""
    # Path to the auth middleware file
    middleware_path = Path("/home/tdeshane/echoforge/app/api/auth_routes.py")
    
    # Check if the middleware file exists
    if not middleware_path.exists():
        # Find the middleware file
        logger.info("Searching for auth middleware file...")
        
        # Common locations for middleware
        possible_paths = [
            Path("/home/tdeshane/echoforge/app/middleware"),
            Path("/home/tdeshane/echoforge/app/core/middleware"),
            Path("/home/tdeshane/echoforge/app/core"),
            Path("/home/tdeshane/echoforge/app")
        ]
        
        middleware_found = False
        for base_path in possible_paths:
            if base_path.exists():
                for file in base_path.glob("**/*.py"):
                    with open(file, "r") as f:
                        content = f.read()
                        if "async def auth_middleware" in content or "def auth_middleware" in content:
                            middleware_path = file
                            middleware_found = True
                            logger.info(f"Found auth middleware in: {middleware_path}")
                            break
            if middleware_found:
                break
        
        if not middleware_found:
            logger.error("❌ Auth middleware file not found")
            return False
    
    # Read the middleware file
    with open(middleware_path, "r") as f:
        content = f.read()
    
    # Check if we need to fix the middleware
    if "async def auth_middleware" in content or "def auth_middleware" in content:
        logger.info("Fixing auth middleware to properly handle sessions")
        
        # Add session handling code
        if "request.cookies.get" not in content or "SESSION_COOKIE_NAME" not in content:
            # Add session cookie handling
            session_code = """
# Add proper session handling
from app.core.auth import SESSION_COOKIE_NAME

# Check for session cookie
session = request.cookies.get(SESSION_COOKIE_NAME)
if session and session.startswith("session_"):
    # Set user in request state for use in routes
    request.state.user = config.AUTH_USERNAME
    is_authenticated = True
"""
            
            # Find the right place to insert the code
            if "is_authenticated = False" in content:
                # Insert after the is_authenticated = False line
                content = re.sub(
                    r"is_authenticated = False",
                    "is_authenticated = False\n" + session_code,
                    content
                )
            elif "async def auth_middleware" in content:
                # Insert after the function definition
                content = re.sub(
                    r"async def auth_middleware\([^)]*\):[^\n]*\n",
                    lambda m: m.group(0) + session_code,
                    content
                )
            
            # Write the updated content
            with open(middleware_path, "w") as f:
                f.write(content)
            
            logger.info(f"✅ Fixed auth middleware in {middleware_path}")
            return True
        else:
            logger.info("Auth middleware already handles sessions correctly")
            return True
    else:
        logger.error(f"❌ Auth middleware function not found in {middleware_path}")
        return False

def fix_login_route():
    """Fix the login route to properly set session cookies."""
    # Path to the auth routes file
    auth_routes_path = Path("/home/tdeshane/echoforge/app/core/auth.py")
    
    # Check if the auth routes file exists
    if not auth_routes_path.exists():
        logger.error(f"❌ Auth routes file not found at {auth_routes_path}")
        return False
    
    # Create a new file with session handling functions
    session_utils_path = Path("/home/tdeshane/echoforge/app/utils/session.py")
    session_utils_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(session_utils_path, "w") as f:
        f.write("""\"\"\"
Session handling utilities for EchoForge
\"\"\"
import secrets
import logging
from fastapi import Response, Request
from app.core.auth import SESSION_COOKIE_NAME

# Setup logging
logger = logging.getLogger(__name__)

def create_session(response: Response, username: str):
    \"\"\"Create a new session for the user and set the cookie.\"\"\"
    # Generate a session token
    session_token = f"session_{secrets.token_hex(16)}"
    
    # Set the session cookie
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        max_age=86400,  # 24 hours in seconds
        expires=86400,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )
    
    logger.info(f"Created session for user: {username}")
    return session_token

def clear_session(response: Response):
    \"\"\"Clear the session cookie.\"\"\"
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    logger.info("Cleared session cookie")
    return True
""")
    
    logger.info(f"✅ Created session utilities in {session_utils_path}")
    
    # Find the UI auth routes file
    ui_auth_routes_path = Path("/home/tdeshane/echoforge/app/ui/auth_routes.py")
    if not ui_auth_routes_path.exists():
        logger.warning(f"⚠️ UI auth routes file not found at {ui_auth_routes_path}")
        return False
    
    if not ui_auth_routes_path:
        logger.warning("⚠️ UI auth routes file not found")
        return False
    
    # Read the UI auth routes file
    with open(ui_auth_routes_path, "r") as f:
        content = f.read()
    
    # Check if we need to fix the login route
    if "def login(" in content:
        logger.info("Fixing login route to properly set session cookies")
        
        # Add import for session utilities
        if "from app.utils.session import" not in content:
            # Add import
            if "import" in content:
                content = re.sub(
                    r"(import [^\n]+)",
                    r"\1\nfrom app.utils.session import create_session, clear_session",
                    content,
                    count=1
                )
            else:
                content = "from app.utils.session import create_session, clear_session\n" + content
        
        # Add session creation to login route
        if "create_session" not in content:
            # Find the login function
            login_pattern = r"(async )?def login\([^)]*\):[^}]*?return response"
            
            # Add session creation before returning response
            content = re.sub(
                login_pattern,
                lambda m: m.group(0).replace(
                    "return response",
                    "# Create session for the user\ncreate_session(response, user.username)\n\nreturn response"
                ),
                content,
                flags=re.DOTALL
            )
        
        # Add session clearing to logout route
        if "def logout(" in content and "clear_session" not in content:
            # Find the logout function
            logout_pattern = r"(async )?def logout\([^)]*\):[^}]*?return response"
            
            # Add session clearing before returning response
            content = re.sub(
                logout_pattern,
                lambda m: m.group(0).replace(
                    "return response",
                    "# Clear user session\nclear_session(response)\n\nreturn response"
                ),
                content,
                flags=re.DOTALL
            )
        
        # Write the updated content
        with open(ui_auth_routes_path, "w") as f:
            f.write(content)
        
        logger.info(f"✅ Fixed auth routes in {ui_auth_routes_path}")
        return True
    else:
        logger.warning(f"⚠️ Login route not found in {ui_auth_routes_path}")
        return False

def main():
    """Main function to fix authentication issues."""
    logger.info("Starting authentication session fixes")
    
    # Fix authentication middleware
    middleware_fixed = fix_auth_middleware()
    
    # Fix login route
    login_fixed = fix_login_route()
    
    if middleware_fixed or login_fixed:
        logger.info("✅ Authentication session fixes completed")
        
        logger.info("\nTo apply the fixes:")
        logger.info("1. Stop the current server: ./stop_server.sh")
        logger.info("2. Start the server again: ./run_server.sh")
        logger.info("3. Test the login functionality")
        
        return True
    else:
        logger.error("❌ No authentication fixes were applied")
        return False

if __name__ == "__main__":
    main()
