"""
Debug authentication routes for testing and troubleshooting.

This module provides debug endpoints for analyzing the session and authentication state.
"""

import logging
import json
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy.orm import Session as SQLAlchemySession

from app.db.session import get_db
from app.core.session import get_session, SESSION_COOKIE_NAME
from app.core.simplified_auth import validate_credentials
from app.core import config

# Setup logging
logger = logging.getLogger("echoforge.debug.auth")

# Create router
router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/session-info")
async def session_info(request: Request, db: SQLAlchemySession = Depends(get_db)):
    """
    Debug endpoint to view session information and authentication state.
    """
    logger.info(f"Debug session info endpoint called")
    
    # Extract all request information
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    all_cookies = request.cookies
    headers = dict(request.headers)
    
    # Get session from database if available
    session_data = None
    if session_id:
        session = get_session(db, session_id)
        if session:
            session_data = session
    
    # Get users from database if available
    users = []
    try:
        # Safely import the User model here to avoid circular imports
        from app.db.models import User
        users_query = db.query(User).all()
        users = [{"id": user.id, "username": user.username, "email": user.email} for user in users_query]
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
    
    # Prepare debug info
    debug_info = {
        "request_info": {
            "path": request.url.path,
            "method": request.method,
            "query_params": dict(request.query_params),
            "cookies": all_cookies,
            "headers": headers
        },
        "session_info": {
            "session_id": session_id,
            "session_data": session_data,
        },
        "auth_config": {
            "auth_enabled": config.ENABLE_AUTH,
            "auth_username": config.AUTH_USERNAME,
            "users_in_db": users
        }
    }
    
    # Log the information for debugging
    logger.info(f"Session debug info: {json.dumps(debug_info, default=str, indent=2)}")
    
    # Return a nice HTML page for browser viewing 
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>EchoForge Auth Debug</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }}
            h1, h2 {{ color: #333; }}
            pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
            .section {{ margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
            button {{ padding: 10px; margin-top: 10px; cursor: pointer; }}
        </style>
    </head>
    <body>
        <h1>EchoForge Authentication Debug Page</h1>
        
        <div class="section">
            <h2>Request Information</h2>
            <pre>{json.dumps(debug_info["request_info"], indent=2)}</pre>
        </div>
        
        <div class="section">
            <h2>Session Information</h2>
            <pre>{json.dumps(debug_info["session_info"], indent=2)}</pre>
        </div>
        
        <div class="section">
            <h2>Auth Configuration</h2>
            <pre>{json.dumps(debug_info["auth_config"], indent=2)}</pre>
        </div>
        
        <div class="section">
            <h2>Login Test</h2>
            <form id="login-form">
                <div>
                    <label for="username">Username:</label>
                    <input type="text" id="username" name="username" value="{config.AUTH_USERNAME}">
                </div>
                <div style="margin-top: 10px;">
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" value="{config.AUTH_PASSWORD}">
                </div>
                <button type="button" onclick="testLogin()">Test Login</button>
            </form>
            <div id="login-result" style="margin-top: 10px;"></div>
        </div>
        
        <script>
            async function testLogin() {{
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const resultDiv = document.getElementById('login-result');
                
                resultDiv.innerHTML = 'Testing login...';
                
                try {{
                    const response = await fetch('/api/auth/login-json', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{ username, password }})
                    }});
                    
                    const data = await response.json();
                    
                    if (response.ok) {{
                        resultDiv.innerHTML = `<div style="color: green;">
                            Login successful: <pre>${{JSON.stringify(data, null, 2)}}</pre>
                        </div>`;
                        
                        // Reload the page after 2 seconds to show the updated session
                        setTimeout(() => {{
                            location.reload();
                        }}, 2000);
                    }} else {{
                        resultDiv.innerHTML = `<div style="color: red;">
                            Login failed: <pre>${{JSON.stringify(data, null, 2)}}</pre>
                        </div>`;
                    }}
                }} catch (error) {{
                    resultDiv.innerHTML = `<div style="color: red;">
                        Error: ${{error.message}}
                    </div>`;
                }}
            }}
        </script>
    </body>
    </html>
    """)

@router.get("/test")
async def test_page():
    """
    Simple test endpoint that always returns success.
    """
    return {"status": "success", "message": "Debug test endpoint working"}
