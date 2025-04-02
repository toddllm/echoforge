# Empty authentication module for EchoForge
# This file contains stub functions to maintain compatibility
# after the authentication system was removed

from fastapi import Depends, Request

# Constants
SESSION_COOKIE_NAME = "echoforge_session"
AUTH_COOKIE_NAME = "echoforge_auth"
AUTH_COOKIE_VALUE = "disabled"

# No-op functions
def verify_credentials(*args, **kwargs):
    return True

def get_current_user(*args, **kwargs):
    return {"username": "user", "disabled": False}

# Dependency that does nothing
def auth_required(request: Request):
    return lambda: None