"""
Tests for the admin UI routes.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
import os
import asyncio
from contextlib import asynccontextmanager

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Return headers with basic auth credentials."""
    return {"Authorization": "Basic ZWNob2ZvcmdlOmNoYW5nZW1lMTIz"}  # echoforge:changeme123


def test_admin_dashboard_unauthorized(client):
    """Test that the admin dashboard requires authentication."""
    # Save the current value of ECHOFORGE_TEST
    original_test_mode = os.environ.get("ECHOFORGE_TEST")
    
    # Disable test mode to ensure authentication is required
    if "ECHOFORGE_TEST" in os.environ:
        del os.environ["ECHOFORGE_TEST"]
    
    try:
        response = client.get("/admin")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    finally:
        # Restore the original test mode setting
        if original_test_mode is not None:
            os.environ["ECHOFORGE_TEST"] = original_test_mode


def test_admin_dashboard_authorized(client, auth_headers):
    """Test that the admin dashboard is accessible with authentication."""
    # Save the current value of ECHOFORGE_TEST
    original_test_mode = os.environ.get("ECHOFORGE_TEST")
    
    # Enable test mode to bypass authentication
    os.environ["ECHOFORGE_TEST"] = "true"
    
    try:
        response = client.get("/admin", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert "Admin Dashboard" in response.text
        assert "Model Status" in response.text
        assert "Active Tasks" in response.text
        assert "Available Voices" in response.text
    finally:
        # Restore the original test mode setting
        if original_test_mode is not None:
            os.environ["ECHOFORGE_TEST"] = original_test_mode
        elif "ECHOFORGE_TEST" in os.environ:
            del os.environ["ECHOFORGE_TEST"]


@patch("app.ui.routes.verify_credentials")
def test_admin_models_page(mock_verify_credentials, client, auth_headers):
    """Test that the admin models page is accessible."""
    # Mock the authentication to return a username
    mock_verify_credentials.return_value = "test_user"
    
    # Save the current value of ECHOFORGE_TEST
    original_test_mode = os.environ.get("ECHOFORGE_TEST")
    
    # Enable test mode to bypass authentication
    os.environ["ECHOFORGE_TEST"] = "true"
    
    try:
        response = client.get("/admin/models", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert "Models" in response.text
    finally:
        # Restore the original test mode setting
        if original_test_mode is not None:
            os.environ["ECHOFORGE_TEST"] = original_test_mode
        elif "ECHOFORGE_TEST" in os.environ:
            del os.environ["ECHOFORGE_TEST"]


@patch("app.ui.routes.verify_credentials")
def test_admin_voices_page(mock_verify_credentials, client, auth_headers):
    """Test that the admin voices page is accessible."""
    # Mock the authentication to return a username
    mock_verify_credentials.return_value = "test_user"
    
    # Save the current value of ECHOFORGE_TEST
    original_test_mode = os.environ.get("ECHOFORGE_TEST")
    
    # Enable test mode to bypass authentication
    os.environ["ECHOFORGE_TEST"] = "true"
    
    try:
        response = client.get("/admin/voices", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert "Voices" in response.text
    finally:
        # Restore the original test mode setting
        if original_test_mode is not None:
            os.environ["ECHOFORGE_TEST"] = original_test_mode
        elif "ECHOFORGE_TEST" in os.environ:
            del os.environ["ECHOFORGE_TEST"]


@patch("app.ui.routes.verify_credentials")
def test_admin_tasks_page(mock_verify_credentials, client, auth_headers):
    """Test that the admin tasks page is accessible."""
    # Mock the authentication to return a username
    mock_verify_credentials.return_value = "test_user"
    
    # Save the current value of ECHOFORGE_TEST
    original_test_mode = os.environ.get("ECHOFORGE_TEST")
    
    # Enable test mode to bypass authentication
    os.environ["ECHOFORGE_TEST"] = "true"
    
    try:
        response = client.get("/admin/tasks", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert "Tasks" in response.text
    finally:
        # Restore the original test mode setting
        if original_test_mode is not None:
            os.environ["ECHOFORGE_TEST"] = original_test_mode
        elif "ECHOFORGE_TEST" in os.environ:
            del os.environ["ECHOFORGE_TEST"]


@patch("app.ui.routes.verify_credentials")
def test_admin_config_page(mock_verify_credentials, client, auth_headers):
    """Test that the admin config page is accessible."""
    # Mock the authentication to return a username
    mock_verify_credentials.return_value = "test_user"
    
    # Save the current value of ECHOFORGE_TEST
    original_test_mode = os.environ.get("ECHOFORGE_TEST")
    
    # Enable test mode to bypass authentication
    os.environ["ECHOFORGE_TEST"] = "true"
    
    try:
        response = client.get("/admin/config", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert "Configuration" in response.text
    finally:
        # Restore the original test mode setting
        if original_test_mode is not None:
            os.environ["ECHOFORGE_TEST"] = original_test_mode
        elif "ECHOFORGE_TEST" in os.environ:
            del os.environ["ECHOFORGE_TEST"]


@patch("app.ui.routes.verify_credentials")
def test_admin_logs_page(mock_verify_credentials, client, auth_headers):
    """Test that the admin logs page is accessible."""
    # Mock the authentication to return a username
    mock_verify_credentials.return_value = "test_user"
    
    # Save the current value of ECHOFORGE_TEST
    original_test_mode = os.environ.get("ECHOFORGE_TEST")
    
    # Enable test mode to bypass authentication
    os.environ["ECHOFORGE_TEST"] = "true"
    
    try:
        response = client.get("/admin/logs", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert "Logs" in response.text
    finally:
        # Restore the original test mode setting
        if original_test_mode is not None:
            os.environ["ECHOFORGE_TEST"] = original_test_mode
        elif "ECHOFORGE_TEST" in os.environ:
            del os.environ["ECHOFORGE_TEST"]


@patch("app.ui.routes.verify_credentials")
def test_admin_dashboard_with_mock_auth(mock_verify_credentials, client):
    """Test admin dashboard with mocked authentication."""
    # Mock the authentication to return a username
    mock_verify_credentials.return_value = "test_user"
    
    # Save the current value of ECHOFORGE_TEST
    original_test_mode = os.environ.get("ECHOFORGE_TEST")
    
    # Enable test mode to bypass authentication
    os.environ["ECHOFORGE_TEST"] = "true"
    
    try:
        response = client.get("/admin")
        assert response.status_code == status.HTTP_200_OK
        assert "Admin Dashboard" in response.text
        
        # Verify that the username is passed to the template
        assert "test_user" in response.text
    finally:
        # Restore the original test mode setting
        if original_test_mode is not None:
            os.environ["ECHOFORGE_TEST"] = original_test_mode
        elif "ECHOFORGE_TEST" in os.environ:
            del os.environ["ECHOFORGE_TEST"]


@patch("app.ui.routes.verify_credentials")
def test_admin_dashboard_system_stats(mock_verify_credentials, client):
    """Test that system stats are passed to the admin dashboard template."""
    mock_verify_credentials.return_value = "test_user"
    
    # Save the current value of ECHOFORGE_TEST
    original_test_mode = os.environ.get("ECHOFORGE_TEST")
    
    # Enable test mode to bypass authentication
    os.environ["ECHOFORGE_TEST"] = "true"
    
    try:
        response = client.get("/admin")
        assert response.status_code == status.HTTP_200_OK
        
        # Check for system stats in the response
        assert "Model Status" in response.text
        assert "Active Tasks" in response.text
        assert "Available Voices" in response.text
        assert "CPU Usage" in response.text
        assert "Memory Usage" in response.text
        assert "GPU Usage" in response.text
        assert "Disk Usage" in response.text
    finally:
        # Restore the original test mode setting
        if original_test_mode is not None:
            os.environ["ECHOFORGE_TEST"] = original_test_mode
        elif "ECHOFORGE_TEST" in os.environ:
            del os.environ["ECHOFORGE_TEST"] 