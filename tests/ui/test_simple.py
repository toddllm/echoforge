"""
Simple tests for the admin UI routes.
"""

import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@patch("app.core.auth.verify_credentials")
def test_admin_dashboard_with_test_mode(mock_verify_credentials, client):
    """Test that the admin dashboard is accessible in test mode."""
    # Mock the authentication to return a username
    mock_verify_credentials.return_value = "test_user"
    
    response = client.get("/admin")
    assert response.status_code == status.HTTP_200_OK
    assert "Admin Dashboard" in response.text 