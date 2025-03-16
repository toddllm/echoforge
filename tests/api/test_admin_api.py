"""
Tests for the admin API endpoints.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Return headers with basic auth credentials."""
    return {
        "Authorization": "Basic ZWNob2ZvcmdlOmNoYW5nZW1lMTIz",  # echoforge:changeme123
        "Content-Type": "application/json"
    }


def test_get_system_stats_unauthorized(client):
    """Test that the system stats endpoint requires authentication."""
    response = client.get("/api/admin/stats")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@patch("app.api.admin.psutil")
@patch("app.api.admin.verify_credentials")
def test_get_system_stats_authorized(mock_verify_credentials, mock_psutil, client, auth_headers):
    """Test that the system stats endpoint returns the expected data."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Mock psutil functions
    mock_psutil.cpu_percent.return_value = 25.5
    mock_psutil.virtual_memory.return_value.percent = 40.2
    mock_psutil.disk_usage.return_value.percent = 30.7
    mock_psutil.boot_time.return_value = datetime.now().timestamp() - 3600  # 1 hour uptime
    
    response = client.get("/api/admin/stats", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "cpu_usage" in data
    assert "memory_usage" in data
    assert "disk_usage" in data
    assert "uptime" in data
    assert "model_loaded" in data
    assert "active_tasks" in data
    assert "completed_tasks" in data
    assert "failed_tasks" in data
    assert "total_voices" in data
    
    # Check specific values
    assert data["cpu_usage"] == 25.5
    assert data["memory_usage"] == 40.2
    assert data["disk_usage"] == 30.7
    assert data["uptime"] > 0


@patch("app.api.admin.voice_generator")
@patch("app.api.admin.verify_credentials")
def test_get_models(mock_verify_credentials, mock_voice_generator, client, auth_headers):
    """Test that the models endpoint returns the expected data."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Mock voice generator
    mock_voice_generator.is_initialized.return_value = True
    mock_voice_generator.device = "cuda"
    
    response = client.get("/api/admin/models", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    model = data[0]
    assert "name" in model
    assert "status" in model
    assert "device" in model
    
    # Check specific values
    assert model["name"] == "CSM Model"
    assert model["status"] == "Loaded"


@patch("app.api.admin.voice_generator")
@patch("app.api.admin.verify_credentials")
def test_load_model(mock_verify_credentials, mock_voice_generator, client, auth_headers):
    """Test that the load model endpoint works as expected."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Mock voice generator
    mock_voice_generator.is_initialized.return_value = False
    
    response = client.post("/api/admin/models/CSM%20Model/load", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "status" in data
    assert "message" in data
    assert data["status"] == "loading"
    
    # Verify that initialize was called
    mock_voice_generator.initialize.assert_called_once()


@patch("app.api.admin.voice_generator")
@patch("app.api.admin.verify_credentials")
def test_unload_model(mock_verify_credentials, mock_voice_generator, client, auth_headers):
    """Test that the unload model endpoint works as expected."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Mock voice generator
    mock_voice_generator.is_initialized.return_value = True
    
    response = client.post("/api/admin/models/CSM%20Model/unload", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "status" in data
    assert "message" in data
    assert data["status"] == "unloaded"
    
    # Verify that shutdown was called
    mock_voice_generator.shutdown.assert_called_once()


@patch("app.api.admin.task_manager")
@patch("app.api.admin.verify_credentials")
def test_get_tasks(mock_verify_credentials, mock_task_manager, client, auth_headers):
    """Test that the tasks endpoint returns the expected data."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Mock task manager
    mock_tasks = {
        "task1": {
            "status": "completed",
            "created_at": datetime.now().timestamp() - 3600,
            "completed_at": datetime.now().timestamp() - 3500,
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
            "created_at": datetime.now().timestamp() - 1800,
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
    
    response = client.get("/api/admin/tasks", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    
    task = data[0]  # First task (sorted by created_at, newest first)
    assert "task_id" in task
    assert "status" in task
    assert "created_at" in task
    assert "progress" in task
    assert "text" in task
    assert "speaker_id" in task
    assert "parameters" in task


@patch("app.api.admin.task_manager")
@patch("app.api.admin.verify_credentials")
def test_cancel_task(mock_verify_credentials, mock_task_manager, client, auth_headers):
    """Test that the cancel task endpoint works as expected."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Mock task manager
    mock_task_manager.task_exists.return_value = True
    
    response = client.delete("/api/admin/tasks/task1", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "status" in data
    assert "message" in data
    assert data["status"] == "cancelled"
    
    # Verify that cancel_task was called with the correct task ID
    mock_task_manager.cancel_task.assert_called_once_with("task1")


@patch("app.api.admin.config")
@patch("app.api.admin.verify_credentials")
def test_get_config(mock_verify_credentials, mock_config, client, auth_headers):
    """Test that the config endpoint returns the expected data."""
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
    
    response = client.get("/api/admin/config", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 9  # At least 9 config settings
    
    # Check for specific settings
    setting_keys = [setting["key"] for setting in data]
    assert "DEFAULT_TEMPERATURE" in setting_keys
    assert "DEFAULT_TOP_K" in setting_keys
    assert "DEFAULT_SPEAKER_ID" in setting_keys
    assert "DEFAULT_STYLE" in setting_keys
    assert "DEFAULT_DEVICE" in setting_keys
    assert "DEFAULT_THEME" in setting_keys
    assert "APP_NAME" in setting_keys
    assert "APP_VERSION" in setting_keys
    assert "OUTPUT_DIR" in setting_keys


@patch("app.api.admin.verify_credentials")
def test_update_config(mock_verify_credentials, client, auth_headers):
    """Test that the update config endpoint works as expected."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    # Test updating a valid setting
    response = client.put(
        "/api/admin/config/DEFAULT_TEMPERATURE",
        headers=auth_headers,
        json=0.8
    )
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "status" in data
    assert "message" in data
    assert data["status"] == "updated"
    
    # Test updating an invalid setting
    response = client.put(
        "/api/admin/config/INVALID_SETTING",
        headers=auth_headers,
        json="invalid"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch("app.api.admin.verify_credentials")
def test_get_logs(mock_verify_credentials, client, auth_headers):
    """Test that the logs endpoint returns the expected data."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    response = client.get("/api/admin/logs", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert isinstance(data, list)
    
    if len(data) > 0:
        log = data[0]
        assert "timestamp" in log
        assert "level" in log
        assert "message" in log
        assert "source" in log


@patch("app.api.admin.verify_credentials")
def test_get_voices(mock_verify_credentials, client, auth_headers):
    """Test that the voices endpoint returns the expected data."""
    # Mock authentication
    mock_verify_credentials.return_value = "test_user"
    
    response = client.get("/api/admin/voices", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert isinstance(data, list)
    
    if len(data) > 0:
        voice = data[0]
        assert "id" in voice
        assert "name" in voice
        assert "gender" in voice
        assert "style" in voice
        assert "sample_count" in voice
        assert "file_path" in voice 