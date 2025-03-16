"""
End-to-end tests for the admin dashboard.

These tests simulate a user interacting with the admin dashboard.
"""

import pytest
import os
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Return headers with basic auth credentials."""
    return {"Authorization": "Basic ZWNob2ZvcmdlOmNoYW5nZW1lMTIz"}  # echoforge:changeme123


@pytest.mark.e2e
@patch("app.api.admin.verify_credentials")
def test_admin_dashboard_navigation(mock_verify_credentials, client, auth_headers):
    """Test navigating through the admin dashboard."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Start at the dashboard
    dashboard_response = client.get("/admin", headers=auth_headers)
    assert dashboard_response.status_code == status.HTTP_200_OK
    assert "Admin Dashboard" in dashboard_response.text
    
    # Navigate to the models page
    models_response = client.get("/admin/models", headers=auth_headers)
    assert models_response.status_code == status.HTTP_200_OK
    assert "Models" in models_response.text
    
    # Navigate to the voices page
    voices_response = client.get("/admin/voices", headers=auth_headers)
    assert voices_response.status_code == status.HTTP_200_OK
    assert "Voices" in voices_response.text
    
    # Navigate to the tasks page
    tasks_response = client.get("/admin/tasks", headers=auth_headers)
    assert tasks_response.status_code == status.HTTP_200_OK
    assert "Tasks" in tasks_response.text
    
    # Navigate to the config page
    config_response = client.get("/admin/config", headers=auth_headers)
    assert config_response.status_code == status.HTTP_200_OK
    assert "Configuration" in config_response.text
    
    # Navigate to the logs page
    logs_response = client.get("/admin/logs", headers=auth_headers)
    assert logs_response.status_code == status.HTTP_200_OK
    assert "Logs" in logs_response.text
    
    # Return to the dashboard
    dashboard_response = client.get("/admin", headers=auth_headers)
    assert dashboard_response.status_code == status.HTTP_200_OK
    assert "Admin Dashboard" in dashboard_response.text


@pytest.mark.e2e
@patch("app.api.admin.voice_generator")
@patch("app.api.admin.verify_credentials")
def test_model_management_workflow(mock_verify_credentials, mock_voice_generator, client, auth_headers):
    """Test the model management workflow."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Mock voice generator
    mock_voice_generator.is_initialized.return_value = True
    mock_voice_generator.device = "cuda"
    
    # Navigate to the models page
    models_response = client.get("/admin/models", headers=auth_headers)
    assert models_response.status_code == status.HTTP_200_OK
    
    # Get the current models
    models_api_response = client.get("/api/admin/models", headers=auth_headers)
    assert models_api_response.status_code == status.HTTP_200_OK
    
    # Unload the model
    unload_response = client.post("/api/admin/models/CSM%20Model/unload", headers=auth_headers)
    assert unload_response.status_code == status.HTTP_200_OK
    
    # Mock that the model is now unloaded
    mock_voice_generator.is_initialized.return_value = False
    
    # Get the updated models
    models_api_response = client.get("/api/admin/models", headers=auth_headers)
    assert models_api_response.status_code == status.HTTP_200_OK
    assert models_api_response.json()[0]["status"] == "Not Loaded"
    
    # Load the model
    load_response = client.post("/api/admin/models/CSM%20Model/load", headers=auth_headers)
    assert load_response.status_code == status.HTTP_200_OK
    
    # Mock that the model is now loaded
    mock_voice_generator.is_initialized.return_value = True
    
    # Get the updated models
    models_api_response = client.get("/api/admin/models", headers=auth_headers)
    assert models_api_response.status_code == status.HTTP_200_OK
    assert models_api_response.json()[0]["status"] == "Loaded"


@pytest.mark.e2e
@patch("app.api.admin.task_manager")
@patch("app.api.admin.verify_credentials")
def test_task_management_workflow(mock_verify_credentials, mock_task_manager, client, auth_headers):
    """Test the task management workflow."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Mock task manager with some tasks
    mock_tasks = {
        "task1": {
            "status": "completed",
            "created_at": time.time() - 3600,
            "completed_at": time.time() - 3500,
            "progress": 100.0,
            "text": "Test text",
            "speaker_id": 1,
            "temperature": 0.7,
            "top_k": 50,
            "style": "default",
            "device": "cpu"
        },
        "task2": {
            "status": "processing",
            "created_at": time.time() - 1800,
            "completed_at": None,
            "progress": 50.0,
            "text": "Another test",
            "speaker_id": 2,
            "temperature": 0.5,
            "top_k": 80,
            "style": "cheerful",
            "device": "cuda"
        }
    }
    mock_task_manager.get_all_tasks.return_value = mock_tasks
    mock_task_manager.task_exists.return_value = True
    
    # Navigate to the tasks page
    tasks_response = client.get("/admin/tasks", headers=auth_headers)
    assert tasks_response.status_code == status.HTTP_200_OK
    
    # Get the current tasks
    tasks_api_response = client.get("/api/admin/tasks", headers=auth_headers)
    assert tasks_api_response.status_code == status.HTTP_200_OK
    assert len(tasks_api_response.json()) == 2
    
    # Cancel a task
    cancel_response = client.delete("/api/admin/tasks/task2", headers=auth_headers)
    assert cancel_response.status_code == status.HTTP_200_OK
    
    # Mock that the task is now cancelled
    mock_tasks["task2"]["status"] = "cancelled"
    
    # Get the updated tasks
    tasks_api_response = client.get("/api/admin/tasks", headers=auth_headers)
    assert tasks_api_response.status_code == status.HTTP_200_OK
    
    # Find the cancelled task
    cancelled_task = next((t for t in tasks_api_response.json() if t["task_id"] == "task2"), None)
    assert cancelled_task is not None
    assert cancelled_task["status"] == "cancelled"


@pytest.mark.e2e
@patch("app.api.admin.config")
@patch("app.api.admin.verify_credentials")
def test_config_management_workflow(mock_verify_credentials, mock_config, client, auth_headers):
    """Test the configuration management workflow."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Mock config values
    mock_config.DEFAULT_TEMPERATURE = 0.7
    mock_config.DEFAULT_TOP_K = 50
    mock_config.DEFAULT_SPEAKER_ID = 1
    mock_config.DEFAULT_STYLE = "default"
    mock_config.DEFAULT_DEVICE = "cpu"
    mock_config.DEFAULT_THEME = "light"
    mock_config.APP_NAME = "EchoForge"
    mock_config.APP_VERSION = "0.1.0"
    mock_config.OUTPUT_DIR = "/tmp/echoforge/voices"
    
    # Navigate to the config page
    config_response = client.get("/admin/config", headers=auth_headers)
    assert config_response.status_code == status.HTTP_200_OK
    
    # Get the current config
    config_api_response = client.get("/api/admin/config", headers=auth_headers)
    assert config_api_response.status_code == status.HTTP_200_OK
    
    # Find the temperature setting
    temp_setting = next((s for s in config_api_response.json() if s["key"] == "DEFAULT_TEMPERATURE"), None)
    assert temp_setting is not None
    assert temp_setting["value"] == 0.7
    
    # Update the temperature setting
    update_response = client.put(
        "/api/admin/config/DEFAULT_TEMPERATURE",
        headers={**auth_headers, "Content-Type": "application/json"},
        json=0.8
    )
    assert update_response.status_code == status.HTTP_200_OK
    
    # Mock that the config value has changed
    mock_config.DEFAULT_TEMPERATURE = 0.8
    
    # Get the updated config
    config_api_response = client.get("/api/admin/config", headers=auth_headers)
    assert config_api_response.status_code == status.HTTP_200_OK
    
    # Find the updated temperature setting
    temp_setting = next((s for s in config_api_response.json() if s["key"] == "DEFAULT_TEMPERATURE"), None)
    assert temp_setting is not None
    assert temp_setting["value"] == 0.8 