"""
Email service for EchoForge.
"""

import os
import logging
from typing import List, Dict, Any
from fastapi import HTTPException

# Use requests for Mailgun API
import requests

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails using Mailgun."""
    
    def __init__(self):
        """Initialize the email service."""
        self.mailgun_api_key = os.environ.get("MAILGUN_API_KEY")
        self.mailgun_domain = os.environ.get("MAILGUN_DOMAIN", "sandbox1234.mailgun.org")
        self.from_email = os.environ.get("FROM_EMAIL", f"postmaster@{self.mailgun_domain}")
        self.app_name = os.environ.get("APP_NAME", "EchoForge")
        self.mailgun_api_url = os.environ.get("MAILGUN_API_URL", "https://api.mailgun.net/v3")
        self.mailgun_base_url = f"{self.mailgun_api_url}/{self.mailgun_domain}"
        
        # Check if Mailgun is configured
        if not self.mailgun_api_key or not self.mailgun_domain:
            logging.warning("Mailgun is not configured. Email functionality will not work.")
            self.is_configured = False
        else:
            self.is_configured = True
            # Log Mailgun configuration
            logging.info(f"Mailgun configured with domain: {self.mailgun_domain}")
            logging.info(f"API key format: {self.mailgun_api_key[:6]}...{self.mailgun_api_key[-4:] if self.mailgun_api_key else 'None'}")
            logging.info(f"Using API URL: {self.mailgun_api_url}")
            logging.info(f"From email: {self.from_email}")
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: str,
        reply_to: str = None,
    ) -> Dict[str, Any]:
        """Send an email using Mailgun REST API directly."""
        if not self.is_configured:
            logger.error("Mailgun is not configured. Email could not be sent.")
            raise HTTPException(status_code=500, detail="Email service is not configured")
        
        # Log Mailgun configuration for debugging
        logger.info("=== Mailgun Configuration ===")
        logger.info(f"API Key: {self.mailgun_api_key[:6]}...{self.mailgun_api_key[-4:] if len(self.mailgun_api_key) > 10 else ''}")
        logger.info(f"Domain: {self.mailgun_domain}")
        logger.info(f"From Email: {self.from_email}")
        logger.info(f"API URL: {self.mailgun_api_url}")
        logger.info(f"Base URL: {self.mailgun_base_url}")
        
        # Prepare email data
        data = {
            'from': f"{self.app_name} <{self.from_email}>",
            'to': to_emails,
            'subject': subject,
            'text': text_content,
            'html': html_content
        }
        
        if reply_to:
            data['h:Reply-To'] = reply_to
        
        logger.info(f"Sending email to: {to_emails}")
        logger.info(f"Email subject: {subject}")
        
        try:
            # Send email using requests
            logger.info(f"Making POST request to: {self.mailgun_base_url}/messages")
            response = requests.post(
                f"{self.mailgun_base_url}/messages",
                auth=("api", self.mailgun_api_key),
                data=data
            )
            
            # Log response details
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {response.headers}")
            
            # Check response
            response.raise_for_status()
            logger.info(f"Email sent successfully: {response.json() if response.text else 'No response text'}")
            return response.json() if response.text else {"message": "Email sent"}
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            logger.error(f"Response content (if available): {getattr(e, 'response', {}).get('text', 'N/A')}")
            raise HTTPException(status_code=500, detail="Failed to send email")
    
    def send_password_reset_email(
        self,
        to_email: str,
        reset_url: str,
        user_name: str = "there"
    ) -> Dict[str, Any]:
        """Send a password reset email."""
        subject = f"Reset Your {self.app_name} Password"
        
        text_content = f"""
Hello {user_name},

You requested to reset your password for your {self.app_name} account. 
Please follow this link to reset your password:

{reset_url}

This link will expire in 1 hour.

If you did not request a password reset, please ignore this email.

Best,
The {self.app_name} Team
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4a90e2; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .button {{ display: inline-block; background-color: #4a90e2; color: white; text-decoration: none; padding: 10px 20px; border-radius: 5px; }}
        .footer {{ text-align: center; margin-top: 20px; font-size: 0.8em; color: #888; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self.app_name}</h1>
        </div>
        <div class="content">
            <p>Hello {user_name},</p>
            <p>You requested to reset your password for your {self.app_name} account.</p>
            <p>Please click the button below to reset your password:</p>
            <p style="text-align: center;">
                <a href="{reset_url}" class="button">Reset Password</a>
            </p>
            <p>Or copy and paste this URL into your browser:</p>
            <p>{reset_url}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you did not request a password reset, please ignore this email.</p>
            <p>Best,<br>The {self.app_name} Team</p>
        </div>
        <div class="footer">
            <p>&copy; {self.app_name} - All rights reserved</p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(
            to_emails=[to_email],
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

# Create a singleton instance
email_service = EmailService()
