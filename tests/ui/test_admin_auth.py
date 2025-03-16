"""
Tests for the admin dashboard's authentication.

These tests verify that the admin dashboard's authentication works correctly.
"""

import pytest
import base64
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.core import config


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


def test_admin_requires_auth(client):
    """Test that the admin dashboard requires authentication."""
    # Try to access the admin dashboard without authentication
    response = client.get("/admin")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Check for WWW-Authenticate header
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_admin_with_valid_credentials(client):
    """Test that the admin dashboard is accessible with valid credentials."""
    # Create valid credentials
    credentials = f"{config.AUTH_USERNAME}:{config.AUTH_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {"Authorization": f"Basic {encoded_credentials}"}
    
    # Access the admin dashboard with valid credentials
    response = client.get("/admin", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert "Admin Dashboard" in response.text


def test_admin_with_invalid_credentials(client):
    """Test that the admin dashboard is not accessible with invalid credentials."""
    # Create invalid credentials
    credentials = "invalid:credentials"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {"Authorization": f"Basic {encoded_credentials}"}
    
    # Try to access the admin dashboard with invalid credentials
    response = client.get("/admin", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_admin_api_requires_auth(client):
    """Test that the admin API endpoints require authentication."""
    # Try to access an admin API endpoint without authentication
    response = client.get("/api/admin/stats")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Check for WWW-Authenticate header
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_admin_api_with_valid_credentials(client):
    """Test that the admin API endpoints are accessible with valid credentials."""
    # Create valid credentials
    credentials = f"{config.AUTH_USERNAME}:{config.AUTH_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {"Authorization": f"Basic {encoded_credentials}"}
    
    # Access an admin API endpoint with valid credentials
    with patch("app.api.admin.verify_credentials", return_value="test_user"):
        response = client.get("/api/admin/stats", headers=headers)
        assert response.status_code == status.HTTP_200_OK


def test_admin_api_with_invalid_credentials(client):
    """Test that the admin API endpoints are not accessible with invalid credentials."""
    # Create invalid credentials
    credentials = "invalid:credentials"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {"Authorization": f"Basic {encoded_credentials}"}
    
    # Try to access an admin API endpoint with invalid credentials
    response = client.get("/api/admin/stats", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@patch("app.core.auth.verify_credentials")
def test_admin_passes_username_to_template(mock_verify_credentials, client):
    """Test that the admin dashboard passes the username to the template."""
    # Mock the authentication to return a username
    mock_verify_credentials.return_value = "test_user"
    
    # Create valid credentials
    credentials = f"{config.AUTH_USERNAME}:{config.AUTH_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {"Authorization": f"Basic {encoded_credentials}"}
    
    # Access the admin dashboard
    response = client.get("/admin", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Check that the username is in the response
    assert "test_user" in response.text


@patch("app.core.auth.config")
def test_admin_auth_respects_enable_auth_setting(mock_config, client):
    """Test that the admin dashboard respects the ENABLE_AUTH setting."""
    # Mock the config to disable authentication
    mock_config.ENABLE_AUTH = False
    mock_config.ALLOW_PUBLIC_SERVING = False
    mock_config.AUTH_REQUIRED_FOR_PUBLIC = False
    
    # Try to access the admin dashboard without authentication
    with patch("app.ui.routes.verify_credentials", return_value="test_user"):
        response = client.get("/admin")
        assert response.status_code == status.HTTP_200_OK
        assert "Admin Dashboard" in response.text
    
    # Mock the config to enable authentication
    mock_config.ENABLE_AUTH = True
    
    # Try to access the admin dashboard without authentication
    response = client.get("/admin")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED 