"""
EchoForge Debug Routes

This module provides debugging endpoints available only in test mode.
These endpoints are meant for development and testing purposes.
"""

import os
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from app.core.test_mode import test_mode
from app.core.simplified_auth import auth_required
from app.db.session import get_db
from sqlalchemy.orm import Session

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/debug",
    tags=["debug"],
)

@router.get("/test-mode-status")
async def test_mode_status():
    """
    Return the current test mode status.
    This endpoint is always accessible regardless of authentication
    and is used to verify test mode configuration.
    """
    env_var = os.environ.get("ECHOFORGE_TEST")
    test_mode_obj = test_mode.is_active
    
    logger.info(f"Debug endpoint accessed - Test mode check: env={env_var}, test_mode.is_active={test_mode_obj}")
    
    return {
        "environment_variable": env_var,
        "test_mode_is_active": test_mode_obj,
        "test_mode_refresh": test_mode._refresh(),
        "environment_variables": {k: v for k, v in os.environ.items() if k.startswith("ECHOFORGE")}
    }

@router.get("/session-info")
async def session_info(request: Request, username: str = Depends(auth_required)):
    """
    Return the current session information.
    This endpoint requires authentication.
    """
    session = getattr(request.state, "session", None)
    
    if not session:
        return {"error": "No session found"}
    
    # Return session info
    return {
        "is_authenticated": session.is_authenticated,
        "user_id": session.user_id,
        "data": session.data
    }

@router.get("/test")
async def test_page():
    """
    Simple test endpoint that always returns success.
    This endpoint does not require authentication and is used to verify the debug routes are working.
    """
    return {"status": "success", "message": "Debug test endpoint working"}

@router.get("/auth-test")
async def auth_test_page():
    """
    Debug page for testing authentication.
    This page provides a simple form to test the login functionality.
    """
    from fastapi.responses import HTMLResponse
    
    return HTMLResponse(content="""
    <html>
    <head>
        <title>EchoForge Auth Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; }
            input[type=text], input[type=password] { width: 300px; padding: 8px; }
            button { padding: 10px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; }
            .results { margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 5px; }
            pre { white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <h1>EchoForge Authentication Test</h1>
        <p>Use this page to test authentication and session functionality.</p>
        
        <div class="form-group">
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" value="admin">
        </div>
        
        <div class="form-group">
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" value="admin">
        </div>
        
        <button onclick="testLogin()">Test Login</button>
        
        <div class="results" id="results">
            <h3>Results will appear here</h3>
        </div>
        
        <script>
            async function testLogin() {
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                
                // Send login request
                try {
                    const response = await fetch('/api/auth/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`,
                        credentials: 'include'
                    });
                    
                    const data = await response.json();
                    displayResult('Login Response', response, data);
                    
                    // If successful, fetch session info
                    if (response.ok) {
                        setTimeout(async () => {
                            try {
                                const sessionResponse = await fetch('/api/debug/session-info', {
                                    credentials: 'include'
                                });
                                const sessionData = await sessionResponse.json();
                                displayResult('Session Info', sessionResponse, sessionData);
                            } catch (error) {
                                displayError('Session Info Error', error);
                            }
                        }, 500);
                    }
                } catch (error) {
                    displayError('Login Error', error);
                }
            }
            
            function displayResult(title, response, data) {
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = `<h3>${title}</h3>
                    <p>Status: ${response.status} ${response.statusText}</p>
                    <pre>${JSON.stringify(data, null, 2)}</pre>`;
            }
            
            function displayError(title, error) {
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = `<h3>${title}</h3>
                    <p>Error: ${error.message}</p>`;
            }
        </script>
    </body>
    </html>
    """)

@router.post("/test-form")
async def test_form_data(username: str = Form(...), password: str = Form(...)):
    """
    Test endpoint for form data processing.
    This helps debug how FastAPI is handling form data submissions.
    """
    logger.info(f"DEBUG - Received form data: username={username}, password_length={len(password)}")
    
    return {
        "received_username": username,
        "received_password_length": len(password),
        "test_mode_active": test_mode.is_active
    }

@router.post("/test-oauth-form")
async def test_oauth_form(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Test endpoint for OAuth2PasswordRequestForm processing.
    This helps debug how FastAPI processes the OAuth2 form specifically.
    """
    logger.info(f"DEBUG - Received OAuth form data: username={form_data.username}, password_length={len(form_data.password)}")
    
    return {
        "received_username": form_data.username,
        "received_password_length": len(form_data.password),
        "test_mode_active": test_mode.is_active,
        "success": True
    }

@router.post("/debug-login")
async def debug_login(request: Request):
    """
    Debug login endpoint that processes raw form data directly.
    This helps identify issues with the auth_routes.py login function.
    """
    try:
        # Get raw form data
        form_data = await request.form()
        logger.info(f"DEBUG LOGIN - Received raw form data: {dict(form_data)}")
        
        # Check test mode
        is_test_mode = os.environ.get("ECHOFORGE_TEST") == "true"
        test_mode_obj_active = test_mode.is_active if hasattr(test_mode, 'is_active') else False
        
        logger.info(f"DEBUG LOGIN - Test mode check: env={is_test_mode}, test_mode.is_active={test_mode_obj_active}")
        
        # Extract username and password
        username = form_data.get("username", "")
        password = form_data.get("password", "")
        
        if is_test_mode or test_mode_obj_active:
            logger.info(f"DEBUG LOGIN - Test mode active, accepting credentials")
            valid_login = True
        else:
            # Normal authentication logic
            from app.core import config
            import secrets
            valid_login = (
                secrets.compare_digest(username, config.AUTH_USERNAME) and 
                secrets.compare_digest(password, config.AUTH_PASSWORD)
            )
            logger.info(f"DEBUG LOGIN - Credential check result: {valid_login}")
        
        if valid_login:
            # Create session data
            session_data = {
                "user_id": username,
                "is_authenticated": True
            }
            
            # Initialize session in the session store if possible
            if hasattr(request, 'state') and hasattr(request.state, 'session'):
                request.state.session.is_authenticated = True
                request.state.session.user_id = username
                logger.info(f"DEBUG LOGIN - Session created for user: {username}")
            
            return {
                "success": True,
                "username": username,
                "test_mode": is_test_mode or test_mode_obj_active,
                "session_created": True
            }
        else:
            return {
                "success": False,
                "detail": "Incorrect username or password",
                "test_mode": is_test_mode or test_mode_obj_active
            }
    except Exception as e:
        logger.error(f"DEBUG LOGIN - Error processing login: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "detail": f"Error: {str(e)}"
        }
