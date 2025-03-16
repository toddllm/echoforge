"""
Tests for the admin dashboard's error handling.

These tests verify that the admin dashboard handles errors correctly.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status, HTTPException

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Return headers with basic auth credentials."""
    return {"Authorization": "Basic ZWNob2ZvcmdlOmNoYW5nZW1lMTIz"}  # echoforge:changeme123


@patch("app.api.admin.voice_generator", None)
@patch("app.api.admin.verify_credentials")
def test_load_model_error_handling(mock_verify_credentials, client, auth_headers):
    """Test that the load model endpoint handles errors correctly."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Try to load a model when voice_generator is None
    response = client.post("/api/admin/models/CSM%20Model/load", headers=auth_headers)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Voice generator not available" in response.json()["detail"]


@patch("app.api.admin.task_manager", None)
@patch("app.api.admin.verify_credentials")
def test_get_tasks_error_handling(mock_verify_credentials, client, auth_headers):
    """Test that the get tasks endpoint handles errors correctly."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Try to get tasks when task_manager is None
    response = client.get("/api/admin/tasks", headers=auth_headers)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Task manager not available" in response.json()["detail"]


@patch("app.api.admin.task_manager")
@patch("app.api.admin.verify_credentials")
def test_cancel_nonexistent_task_error_handling(mock_verify_credentials, mock_task_manager, client, auth_headers):
    """Test that the cancel task endpoint handles nonexistent tasks correctly."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Mock task_manager to return False for task_exists
    mock_task_manager.task_exists.return_value = False
    
    # Try to cancel a nonexistent task
    response = client.delete("/api/admin/tasks/nonexistent_task", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Task not found" in response.json()["detail"]


@patch("app.api.admin.verify_credentials")
def test_update_invalid_config_error_handling(mock_verify_credentials, client, auth_headers):
    """Test that the update config endpoint handles invalid settings correctly."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Try to update an invalid setting
    response = client.put(
        "/api/admin/config/INVALID_SETTING",
        headers={**auth_headers, "Content-Type": "application/json"},
        json="invalid"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Setting not found or not editable" in response.json()["detail"]


@patch("app.ui.routes.templates", None)
@patch("app.ui.routes.verify_credentials")
def test_admin_dashboard_template_error_handling(mock_verify_credentials, client, auth_headers):
    """Test that the admin dashboard handles template errors correctly."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Try to access the admin dashboard when templates is None
    with pytest.raises(Exception):
        response = client.get("/admin", headers=auth_headers)


@patch("app.api.admin.voice_generator")
@patch("app.api.admin.verify_credentials")
def test_unload_model_not_loaded_error_handling(mock_verify_credentials, mock_voice_generator, client, auth_headers):
    """Test that the unload model endpoint handles not loaded models correctly."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Mock voice_generator to return False for is_initialized
    mock_voice_generator.is_initialized.return_value = False
    
    # Try to unload a model that is not loaded
    response = client.post("/api/admin/models/CSM%20Model/unload", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "not_loaded"
    assert "Model is not loaded" in response.json()["message"]


@patch("app.api.admin.voice_generator")
@patch("app.api.admin.verify_credentials")
def test_load_model_already_loaded_error_handling(mock_verify_credentials, mock_voice_generator, client, auth_headers):
    """Test that the load model endpoint handles already loaded models correctly."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Mock voice_generator to return True for is_initialized
    mock_voice_generator.is_initialized.return_value = True
    
    # Try to load a model that is already loaded
    response = client.post("/api/admin/models/CSM%20Model/load", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "already_loaded"
    assert "Model is already loaded" in response.json()["message"]


@patch("app.main.general_exception_handler")
def test_global_exception_handler(mock_exception_handler, client):
    """Test that the global exception handler works correctly."""
    # Mock the exception handler to return a specific response
    mock_response = MagicMock()
    mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    mock_response.json.return_value = {"detail": "Test error"}
    mock_exception_handler.return_value = mock_response
    
    # Create a route that raises an exception
    @app.get("/test-error")
    def test_error():
        raise Exception("Test error")
    
    # Access the route
    response = client.get("/test-error")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Test error" in response.json()["detail"] 