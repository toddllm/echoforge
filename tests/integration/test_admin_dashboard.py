"""
Integration tests for the admin dashboard.

These tests verify that the admin dashboard works correctly with the API endpoints.
"""

import pytest
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


@patch("app.api.admin.psutil")
@patch("app.api.admin.verify_credentials")
def test_dashboard_with_api_integration(mock_verify_credentials, mock_psutil, client, auth_headers):
    """Test that the admin dashboard integrates with the API endpoints."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Mock psutil functions for system stats
    mock_psutil.cpu_percent.return_value = 25.5
    mock_psutil.virtual_memory.return_value.percent = 40.2
    mock_psutil.disk_usage.return_value.percent = 30.7
    mock_psutil.boot_time.return_value = 0  # Just for testing
    
    # First, access the dashboard page
    dashboard_response = client.get("/admin", headers=auth_headers)
    assert dashboard_response.status_code == status.HTTP_200_OK
    
    # Then, access the API endpoint for system stats
    stats_response = client.get("/api/admin/stats", headers=auth_headers)
    assert stats_response.status_code == status.HTTP_200_OK
    
    # Verify that the API returns the expected data
    stats_data = stats_response.json()
    assert stats_data["cpu_usage"] == 25.5
    assert stats_data["memory_usage"] == 40.2
    assert stats_data["disk_usage"] == 30.7


@patch("app.api.admin.voice_generator")
@patch("app.api.admin.verify_credentials")
def test_model_management_integration(mock_verify_credentials, mock_voice_generator, client, auth_headers):
    """Test that the model management page integrates with the API endpoints."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Mock voice generator
    mock_voice_generator.is_initialized.return_value = True
    mock_voice_generator.device = "cuda"
    
    # First, access the models page
    models_page_response = client.get("/admin/models", headers=auth_headers)
    assert models_page_response.status_code == status.HTTP_200_OK
    
    # Then, access the API endpoint for models
    models_response = client.get("/api/admin/models", headers=auth_headers)
    assert models_response.status_code == status.HTTP_200_OK
    
    # Verify that the API returns the expected data
    models_data = models_response.json()
    assert len(models_data) > 0
    assert models_data[0]["name"] == "CSM Model"
    assert models_data[0]["status"] == "Loaded"
    
    # Test unloading the model
    mock_voice_generator.is_initialized.return_value = True
    unload_response = client.post("/api/admin/models/CSM%20Model/unload", headers=auth_headers)
    assert unload_response.status_code == status.HTTP_200_OK
    assert unload_response.json()["status"] == "unloaded"
    mock_voice_generator.shutdown.assert_called_once()
    
    # Test loading the model
    mock_voice_generator.is_initialized.return_value = False
    load_response = client.post("/api/admin/models/CSM%20Model/load", headers=auth_headers)
    assert load_response.status_code == status.HTTP_200_OK
    assert load_response.json()["status"] == "loading"
    # The initialize method should be called via background tasks, which we can't easily verify in tests


@patch("app.api.admin.task_manager")
@patch("app.api.admin.verify_credentials")
def test_task_management_integration(mock_verify_credentials, mock_task_manager, client, auth_headers):
    """Test that the task management page integrates with the API endpoints."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Mock task manager with some tasks
    mock_tasks = {
        "task1": {
            "status": "completed",
            "created_at": 1000000000,
            "completed_at": 1000000100,
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
            "created_at": 1000001000,
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
    
    # First, access the tasks page
    tasks_page_response = client.get("/admin/tasks", headers=auth_headers)
    assert tasks_page_response.status_code == status.HTTP_200_OK
    
    # Then, access the API endpoint for tasks
    tasks_response = client.get("/api/admin/tasks", headers=auth_headers)
    assert tasks_response.status_code == status.HTTP_200_OK
    
    # Verify that the API returns the expected data
    tasks_data = tasks_response.json()
    assert len(tasks_data) == 2
    
    # Test cancelling a task
    cancel_response = client.delete("/api/admin/tasks/task1", headers=auth_headers)
    assert cancel_response.status_code == status.HTTP_200_OK
    assert cancel_response.json()["status"] == "cancelled"
    mock_task_manager.cancel_task.assert_called_once_with("task1")


@patch("app.api.admin.config")
@patch("app.api.admin.verify_credentials")
def test_config_management_integration(mock_verify_credentials, mock_config, client, auth_headers):
    """Test that the config management page integrates with the API endpoints."""
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
    
    # First, access the config page
    config_page_response = client.get("/admin/config", headers=auth_headers)
    assert config_page_response.status_code == status.HTTP_200_OK
    
    # Then, access the API endpoint for config
    config_response = client.get("/api/admin/config", headers=auth_headers)
    assert config_response.status_code == status.HTTP_200_OK
    
    # Verify that the API returns the expected data
    config_data = config_response.json()
    assert len(config_data) >= 9
    
    # Test updating a config setting
    update_response = client.put(
        "/api/admin/config/DEFAULT_TEMPERATURE",
        headers={**auth_headers, "Content-Type": "application/json"},
        json=0.8
    )
    assert update_response.status_code == status.HTTP_200_OK
    assert update_response.json()["status"] == "updated"


@patch("app.api.admin.verify_credentials")
def test_logs_viewer_integration(mock_verify_credentials, client, auth_headers):
    """Test that the logs viewer page integrates with the API endpoints."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # First, access the logs page
    logs_page_response = client.get("/admin/logs", headers=auth_headers)
    assert logs_page_response.status_code == status.HTTP_200_OK
    
    # Then, access the API endpoint for logs
    logs_response = client.get("/api/admin/logs", headers=auth_headers)
    assert logs_response.status_code == status.HTTP_200_OK
    
    # Verify that the API returns the expected data format
    logs_data = logs_response.json()
    assert isinstance(logs_data, list)


@patch("app.api.admin.verify_credentials")
def test_voices_management_integration(mock_verify_credentials, client, auth_headers):
    """Test that the voices management page integrates with the API endpoints."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # First, access the voices page
    voices_page_response = client.get("/admin/voices", headers=auth_headers)
    assert voices_page_response.status_code == status.HTTP_200_OK
    
    # Then, access the API endpoint for voices
    voices_response = client.get("/api/admin/voices", headers=auth_headers)
    assert voices_response.status_code == status.HTTP_200_OK
    
    # Verify that the API returns the expected data format
    voices_data = voices_response.json()
    assert isinstance(voices_data, list) 