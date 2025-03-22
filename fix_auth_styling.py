#!/usr/bin/env python
"""
Fix styling issues in EchoForge authentication forms
"""
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def update_file(file_path, original_content, new_content):
    """Update file content if changed"""
    if original_content != new_content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        logger.info(f"✅ Updated {file_path}")
        return True
    else:
        logger.info(f"No changes needed for {file_path}")
        return False

def fix_login_template():
    """Fix styling in login template"""
    login_file = Path("templates/auth/login.html")
    
    if not login_file.exists():
        logger.error(f"❌ Login template not found: {login_file}")
        return False
    
    with open(login_file, 'r') as f:
        content = f.read()
    
    # Update column classes for better responsive layout
    updated_content = content.replace(
        '<div class="col-12 col-sm-10 col-md-8 col-lg-5 col-xl-4">',
        '<div class="col-12 col-sm-10 col-md-6 col-lg-4 col-xl-3">'
    )
    
    return update_file(login_file, content, updated_content)

def fix_signup_template():
    """Fix styling in signup template"""
    signup_file = Path("templates/auth/signup.html")
    
    if not signup_file.exists():
        logger.error(f"❌ Signup template not found: {signup_file}")
        return False
    
    with open(signup_file, 'r') as f:
        content = f.read()
    
    # Update column classes for better responsive layout
    updated_content = content.replace(
        '<div class="col-12 col-sm-10 col-md-8 col-lg-5 col-xl-4">',
        '<div class="col-12 col-sm-10 col-md-6 col-lg-4 col-xl-3">'
    )
    
    return update_file(signup_file, content, updated_content)

def fix_css_styling():
    """Fix CSS styling for auth forms"""
    css_file = Path("static/css/styles.css")
    
    if not css_file.exists():
        logger.error(f"❌ CSS file not found: {css_file}")
        return False
    
    with open(css_file, 'r') as f:
        content = f.read()
    
    # Add improved auth form styling
    if ".auth-card" in content:
        # Add improved auth card styling
        auth_card_css = """
/* Improved auth card styling */
.auth-card {
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
    border-radius: 0.5rem;
    overflow: hidden;
}

.auth-card .card-body {
    padding: 1.25rem;
}

@media (min-width: 768px) {
    .auth-card .card-body {
        padding: 1.5rem;
    }
}

.auth-card .form-control {
    height: auto;
    padding: 0.5rem 0.75rem;
    font-size: 0.9rem;
    line-height: 1.5;
    border-radius: 0.25rem;
    margin-bottom: 1rem;
    border-width: 1px;
    transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.auth-card h2 {
    font-size: 1.4rem;
    margin-bottom: 1rem;
    font-weight: 600;
}

.auth-card .form-group {
    margin-bottom: 1rem;
}

.auth-card .btn-primary {
    padding: 0.5rem 1rem;
    font-size: 0.9rem;
}

@media (max-width: 576px) {
    .auth-card .card-body {
        padding: 1rem;
    }
    
    .auth-card h2 {
        font-size: 1.2rem;
    }
    
    .auth-card .form-control {
        padding: 0.4rem 0.6rem;
    }
}

.auth-container {
    display: flex;
    min-height: calc(100vh - 60px);
    align-items: center;
}
"""
        
        # Check if we need to replace existing auth card styles or add new ones
        if ".auth-card {" in content:
            # Find the start of the auth card styles
            start_idx = content.find(".auth-card {")
            # Find the end of the auth card styles section
            end_idx = content.find("}", start_idx)
            
            # If we found both start and end, replace the section
            if start_idx != -1 and end_idx != -1:
                # Find the next style after auth-card section
                next_style_idx = content.find(".", end_idx)
                if next_style_idx != -1:
                    # Replace all auth-card related styles
                    updated_content = content[:start_idx] + auth_card_css + content[next_style_idx:]
                else:
                    # If no next style, append to the end
                    updated_content = content[:start_idx] + auth_card_css
            else:
                # If we couldn't find the exact section, append to the end
                updated_content = content + "\n" + auth_card_css
        else:
            # If no auth card styles exist, append to the end
            updated_content = content + "\n" + auth_card_css
        
        return update_file(css_file, content, updated_content)
    else:
        logger.error("❌ Could not find auth card styles in CSS file")
        return False

def main():
    """Main function to fix auth form styling"""
    logger.info("Starting auth form styling fix")
    
    # Change to the project root directory
    os.chdir(Path(__file__).parent)
    
    # Fix login template
    login_fixed = fix_login_template()
    
    # Fix signup template
    signup_fixed = fix_signup_template()
    
    # Fix CSS styling
    css_fixed = fix_css_styling()
    
    if login_fixed or signup_fixed or css_fixed:
        logger.info("✅ Auth form styling fixed successfully")
        return True
    else:
        logger.info("❌ No styling changes were made")
        return False

if __name__ == "__main__":
    main()
