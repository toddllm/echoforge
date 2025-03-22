#!/usr/bin/env python
"""
Fix authentication cookie handling in EchoForge
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

def fix_login_endpoint():
    """Fix the login endpoint to set a session cookie."""
    # Path to the auth API routes file
    auth_routes_path = Path("/home/tdeshane/echoforge/app/api/auth_routes.py")
    
    if not auth_routes_path.exists():
        logger.error(f"❌ Auth routes file not found at {auth_routes_path}")
        return False
    
    # Read the auth routes file
    with open(auth_routes_path, "r") as f:
        content = f.read()
    
    # Check if we need to update the login endpoint
    if "@router.post(\"/login\")" in content and "response: JSONResponse" not in content:
        logger.info("Updating login endpoint to set session cookie")
        
        # Update the login function signature to include Response
        content = content.replace(
            "@router.post(\"/login\")\nasync def login(form_data: OAuth2PasswordRequestForm = Depends()):",
            "@router.post(\"/login\")\nasync def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):"
        )
        
        # Add import for Response if needed
        if "from fastapi.responses import JSONResponse" in content:
            content = content.replace(
                "from fastapi.responses import JSONResponse",
                "from fastapi.responses import JSONResponse, Response"
            )
        else:
            content = content.replace(
                "from fastapi import APIRouter",
                "from fastapi import APIRouter, Response"
            )
        
        # Update the return statement to set a cookie
        if "return {" in content:
            # Find the return statement in the login function
            login_return_pattern = r"return\s*{\s*\"access_token\":[^}]*}"
            
            # Replace it with a version that sets a cookie
            cookie_return = """
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
    
    return response"""
            
            # Replace the return statement
            content = re.sub(
                login_return_pattern,
                lambda m: "    token = \"dummy_token_\" + secrets.token_hex(16)\n" + cookie_return,
                content,
                flags=re.DOTALL
            )
        
        # Write the updated content
        with open(auth_routes_path, "w") as f:
            f.write(content)
        
        logger.info(f"✅ Updated login endpoint in {auth_routes_path}")
        return True
    else:
        logger.info("Login endpoint already sets a session cookie or has a different format")
        return False

def fix_logout_endpoint():
    """Fix the logout endpoint to clear the session cookie."""
    # Path to the auth API routes file
    auth_routes_path = Path("/home/tdeshane/echoforge/app/api/auth_routes.py")
    
    if not auth_routes_path.exists():
        logger.error(f"❌ Auth routes file not found at {auth_routes_path}")
        return False
    
    # Read the auth routes file
    with open(auth_routes_path, "r") as f:
        content = f.read()
    
    # Check if we need to update the logout endpoint
    if "@router.post(\"/logout\")" in content and "set_cookie" not in content:
        logger.info("Updating logout endpoint to clear session cookie")
        
        # Update the logout function signature to include Response
        content = content.replace(
            "@router.post(\"/logout\")\nasync def logout():",
            "@router.post(\"/logout\")\nasync def logout(response: Response):"
        )
        
        # Add import for Response if needed
        if "from fastapi.responses import Response" not in content:
            if "from fastapi.responses import" in content:
                content = content.replace(
                    "from fastapi.responses import",
                    "from fastapi.responses import Response, "
                )
            else:
                content = content.replace(
                    "from fastapi import APIRouter",
                    "from fastapi import APIRouter, Response"
                )
        
        # Update the return statement to clear the cookie
        if "return {\"message\": \"Logged out successfully\"}" in content:
            content = content.replace(
                "return {\"message\": \"Logged out successfully\"}",
                """# Clear session cookie
    response.delete_cookie(key="echoforge_session")
    
    return {\"message\": \"Logged out successfully\"}"""
            )
        
        # Write the updated content
        with open(auth_routes_path, "w") as f:
            f.write(content)
        
        logger.info(f"✅ Updated logout endpoint in {auth_routes_path}")
        return True
    else:
        logger.info("Logout endpoint already clears the session cookie or has a different format")
        return False

def main():
    """Main function to fix authentication cookie issues."""
    logger.info("Starting authentication cookie fixes")
    
    # Fix login endpoint
    login_fixed = fix_login_endpoint()
    
    # Fix logout endpoint
    logout_fixed = fix_logout_endpoint()
    
    if login_fixed or logout_fixed:
        logger.info("✅ Authentication cookie fixes completed successfully")
        
        logger.info("\nTo apply the fixes:")
        logger.info("1. Stop the current server: ./stop_server.sh")
        logger.info("2. Start the server again: ./run_server.sh")
        logger.info("3. Test the login functionality")
        
        return True
    else:
        logger.error("❌ No authentication cookie fixes were applied")
        return False

if __name__ == "__main__":
    main()
