"""
Test mode middleware to handle auth bypass in test environment.
"""

import os
import secrets
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger("echoforge.middleware.test_mode")

class TestModeMiddleware(BaseHTTPMiddleware):
    """Middleware to intercept auth requests in test mode and provide dummy credentials."""
    
    async def dispatch(self, request: Request, call_next):
        """Process incoming requests and check for test mode auth bypass."""
        # Check if test mode is active
        is_test_mode = os.environ.get("ECHOFORGE_TEST") == "true"
        
        # Only intercept login requests in test mode
        if is_test_mode and request.url.path == "/api/auth/login":
            logger.info(f"TestModeMiddleware: Intercepting login request in test mode")
            
            # Extract 'next' parameter from query params if present
            next_url = None
            if request.query_params and "next" in request.query_params:
                next_url = request.query_params.get("next")
                logger.info(f"TestModeMiddleware: Found next URL in query params: {next_url}")
            
            # Check form data for 'next' parameter if not in query params
            if not next_url:
                try:
                    # Clone the request to avoid consuming the body
                    body = await request.body()
                    form_data = await request.form()
                    form_dict = dict(form_data)
                    
                    if "next" in form_dict:
                        next_url = form_dict.get("next")
                        logger.info(f"TestModeMiddleware: Found next URL in form data: {next_url}")
                except Exception as e:
                    logger.error(f"TestModeMiddleware: Error extracting form data: {str(e)}")
            
            # Create dummy auth response
            token = "test_token_" + secrets.token_hex(16)
            session_id = "test_session_" + secrets.token_hex(16)
            
            # Initialize session if available
            if hasattr(request, 'state') and hasattr(request.state, 'session'):
                session = request.state.session
                session.is_authenticated = True
                session.user_id = "echoforge"
                session.data['theme_preference'] = "dark"
                logger.info("TestModeMiddleware: Set session data for test mode")
            
            # Create response
            response = JSONResponse(content={
                "access_token": token,
                "token_type": "bearer",
                "username": "echoforge",
                "test_mode": True,
                "test_middleware": True,
                "success": True
            })
            
            # Set session cookie
            response.set_cookie(
                key="echoforge_session",
                value=session_id,
                httponly=True,
                max_age=86400,
                secure=False
            )
            
            # Add X-Next-URL header if 'next' parameter was provided
            if next_url:
                response.headers["X-Next-URL"] = next_url
                # Also set lowercase header for compatibility
                response.headers["x-next-url"] = next_url
                logger.info(f"TestModeMiddleware: Added X-Next-URL header: {next_url}")
            
            logger.info("TestModeMiddleware: Returning test auth response")
            return response
        
        # Process normally for non-login requests or non-test mode
        return await call_next(request)
