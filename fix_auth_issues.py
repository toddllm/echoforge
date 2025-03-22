#!/usr/bin/env python
"""
Fix authentication issues in the EchoForge application
"""
import os
import logging
import requests
from pathlib import Path
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def fix_auth_routes():
    """Fix authentication routes and session handling."""
    # Path to the auth routes file
    auth_routes_path = Path("/home/tdeshane/echoforge/app/core/auth.py")
    
    if not auth_routes_path.exists():
        logger.error(f"❌ Auth routes file not found at {auth_routes_path}")
        return False
    
    # Read the current content
    with open(auth_routes_path, "r") as f:
        content = f.read()
    
    # Check if we need to fix the login route
    if "def login(" in content:
        logger.info("Fixing login route to properly set session cookie")
        
        # Look for the login function and ensure it sets the session properly
        if "response.set_cookie" not in content:
            # Add code to set the session cookie properly
            login_function_fixed = """@router.post("/login")
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"}
        )
    
    # Create access token with extended expiration
    access_token_expires = timedelta(hours=24)  # Longer session time
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Set secure cookie with the token
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=86400,  # 24 hours in seconds
        expires=86400,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )
    
    # Set session in the request for immediate use
    request.session["user"] = user.username
    
    # Redirect to home page after successful login
    response = RedirectResponse(url="/", status_code=303)
    return response"""
            
            # Replace the login function
            import re
            pattern = r"@router\.post\(\"/login\"\)[\s\S]+?return response"
            content = re.sub(pattern, login_function_fixed, content)
            
            # Write the updated content
            with open(auth_routes_path, "w") as f:
                f.write(content)
            
            logger.info("✅ Fixed login route to properly set session cookie")
        else:
            logger.info("Login route already sets session cookie properly")
    
    # Fix the middleware to properly check authentication
    middleware_path = Path("/home/tdeshane/echoforge/app/middleware/auth.py")
    if middleware_path.exists():
        logger.info("Fixing authentication middleware")
        
        with open(middleware_path, "r") as f:
            middleware_content = f.read()
        
        # Check if we need to fix the middleware
        if "async def auth_middleware" in middleware_content:
            # Add improved authentication middleware
            improved_middleware = """async def auth_middleware(request: Request, call_next):
    # Public paths that don't require authentication
    public_paths = [
        "/login", "/auth/login", "/logout", "/auth/logout", 
        "/signup", "/auth/signup", "/forgot-password", "/auth/forgot-password",
        "/reset-password", "/auth/reset-password", "/static/", "/favicon.ico"
    ]
    
    # Check if the path is public
    is_public_path = any(request.url.path.startswith(path) for path in public_paths)
    
    # Get the token from the cookie
    token = request.cookies.get("access_token")
    
    # Initialize authentication status
    is_authenticated = False
    
    # Verify the token if it exists
    if token and token.startswith("Bearer "):
        try:
            token_data = verify_token(token.replace("Bearer ", ""))
            if token_data:
                # Set the user in the session
                request.session["user"] = token_data.username
                is_authenticated = True
        except Exception as e:
            logger.error(f"Token verification error: {e}")
    
    # If not authenticated and not a public path, redirect to login
    if not is_authenticated and not is_public_path:
        logger.info("User not authenticated, redirecting to login")
        return RedirectResponse(url="/login", status_code=303)
    
    # Continue with the request
    response = await call_next(request)
    return response"""
            
            # Replace the middleware function
            import re
            pattern = r"async def auth_middleware[\s\S]+?return response"
            middleware_content = re.sub(pattern, improved_middleware, middleware_content)
            
            # Write the updated content
            with open(middleware_path, "w") as f:
                f.write(middleware_content)
            
            logger.info("✅ Fixed authentication middleware")
        else:
            logger.info("Authentication middleware not found, may be in a different file")
    
    return True

def fix_auth_styling():
    """Fix styling for login and signup forms."""
    # Paths to the template files
    login_template_path = Path("/home/tdeshane/echoforge/templates/auth/login.html")
    signup_template_path = Path("/home/tdeshane/echoforge/templates/auth/signup.html")
    
    # Fix login template
    if login_template_path.exists():
        logger.info("Fixing login template styling")
        
        with open(login_template_path, "r") as f:
            login_content = f.read()
        
        # Parse the HTML
        soup = BeautifulSoup(login_content, "html.parser")
        
        # Find the main container div
        container = soup.find("div", class_="container")
        if container:
            # Update the container classes
            container["class"] = "container d-flex justify-content-center align-items-center min-vh-100"
            
            # Find the card div
            card = container.find("div", class_="card")
            if card:
                # Update the card classes and style
                card["class"] = "card bg-dark text-light shadow-lg"
                card["style"] = "max-width: 400px; width: 100%;"
                
                # Find the card body
                card_body = card.find("div", class_="card-body")
                if card_body:
                    # Update the card body padding
                    card_body["class"] = "card-body p-4"
                    
                    # Find the title and update it
                    title = card_body.find("h2")
                    if title:
                        title["class"] = "text-center mb-4 text-primary"
                
                # Write the updated content
                with open(login_template_path, "w") as f:
                    f.write(str(soup))
                
                logger.info("✅ Fixed login template styling")
            else:
                logger.warning("Card div not found in login template")
        else:
            logger.warning("Container div not found in login template")
    
    # Fix signup template
    if signup_template_path.exists():
        logger.info("Fixing signup template styling")
        
        with open(signup_template_path, "r") as f:
            signup_content = f.read()
        
        # Parse the HTML
        soup = BeautifulSoup(signup_content, "html.parser")
        
        # Find the main container div
        container = soup.find("div", class_="container")
        if container:
            # Update the container classes
            container["class"] = "container d-flex justify-content-center align-items-center min-vh-100"
            
            # Find the card div
            card = container.find("div", class_="card")
            if card:
                # Update the card classes and style
                card["class"] = "card bg-dark text-light shadow-lg"
                card["style"] = "max-width: 400px; width: 100%;"
                
                # Find the card body
                card_body = card.find("div", class_="card-body")
                if card_body:
                    # Update the card body padding
                    card_body["class"] = "card-body p-4"
                    
                    # Find the title and update it
                    title = card_body.find("h2")
                    if title:
                        title["class"] = "text-center mb-4 text-primary"
                
                # Write the updated content
                with open(signup_template_path, "w") as f:
                    f.write(str(soup))
                
                logger.info("✅ Fixed signup template styling")
            else:
                logger.warning("Card div not found in signup template")
        else:
            logger.warning("Container div not found in signup template")
    
    # Add custom CSS for auth forms
    css_path = Path("/home/tdeshane/echoforge/static/css/auth.css")
    css_dir = css_path.parent
    
    # Create the directory if it doesn't exist
    css_dir.mkdir(parents=True, exist_ok=True)
    
    # Create or update the CSS file
    with open(css_path, "w") as f:
        f.write("""/* Auth forms styling */
.auth-card {
    max-width: 400px;
    width: 100%;
    background-color: #2d2d2d;
    border: none;
    border-radius: 10px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.auth-card .card-header {
    background-color: #3a3a3a;
    border-bottom: 1px solid #444;
    border-radius: 10px 10px 0 0;
}

.auth-card .card-body {
    padding: 2rem;
}

.auth-card .form-control {
    background-color: #3a3a3a;
    border: 1px solid #444;
    color: #fff;
    transition: all 0.3s ease;
}

.auth-card .form-control:focus {
    background-color: #3a3a3a;
    border-color: #4a6fdc;
    box-shadow: 0 0 0 0.25rem rgba(74, 111, 220, 0.25);
    color: #fff;
}

.auth-card .btn-primary {
    background-color: #4a6fdc;
    border-color: #4a6fdc;
    width: 100%;
    padding: 0.6rem;
    font-weight: 500;
    transition: all 0.3s ease;
}

.auth-card .btn-primary:hover {
    background-color: #3a5fc9;
    border-color: #3a5fc9;
}

.auth-card a {
    color: #4a6fdc;
    text-decoration: none;
    transition: all 0.3s ease;
}

.auth-card a:hover {
    color: #3a5fc9;
    text-decoration: underline;
}

.auth-title {
    color: #4a6fdc;
    font-weight: 600;
    margin-bottom: 1.5rem;
    text-align: center;
}

.auth-subtitle {
    color: #aaa;
    font-size: 0.9rem;
    text-align: center;
    margin-bottom: 1.5rem;
}

.form-floating > .form-control {
    height: calc(3.5rem + 2px);
    line-height: 1.25;
}

.form-floating > label {
    padding: 1rem 0.75rem;
}

.auth-footer {
    text-align: center;
    padding-top: 1rem;
    border-top: 1px solid #444;
    margin-top: 1.5rem;
}
""")
    
    logger.info("✅ Created custom CSS for auth forms")
    
    return True

def main():
    """Main function to fix authentication issues."""
    logger.info("Starting authentication fixes")
    
    # Fix authentication routes
    auth_routes_fixed = fix_auth_routes()
    
    # Fix authentication styling
    auth_styling_fixed = fix_auth_styling()
    
    if auth_routes_fixed and auth_styling_fixed:
        logger.info("✅ Authentication fixes completed successfully")
        
        logger.info("\nTo apply the fixes:")
        logger.info("1. Stop the current server: ./stop_server.sh")
        logger.info("2. Start the server again: ./run_server.sh")
        logger.info("3. Test the login functionality")
        
        return True
    else:
        logger.error("❌ Some authentication fixes failed")
        return False

if __name__ == "__main__":
    main()
