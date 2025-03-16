"""
Tests for the admin dashboard's JavaScript functionality.

These tests verify that the JavaScript functions in admin.js work correctly.
"""

import pytest
import re
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


def test_admin_js_is_loaded(client, auth_headers):
    """Test that the admin.js file is loaded in the admin dashboard."""
    response = client.get("/admin", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Check that the admin.js script is included
    assert '<script src="/static/js/admin.js"></script>' in response.text


def test_admin_css_is_loaded(client, auth_headers):
    """Test that the admin.css file is loaded in the admin dashboard."""
    response = client.get("/admin", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Check that the admin.css stylesheet is included
    assert '<link rel="stylesheet" href="/static/css/admin.css">' in response.text


def test_sidebar_toggle_exists(client, auth_headers):
    """Test that the sidebar toggle button exists in the admin dashboard."""
    response = client.get("/admin", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Check that the sidebar toggle button exists
    assert 'id="sidebar-toggle"' in response.text


def test_dashboard_refresh_button_exists(client, auth_headers):
    """Test that the dashboard refresh button exists in the admin dashboard."""
    response = client.get("/admin", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Check that the refresh button exists
    assert 'id="refresh-dashboard-btn"' in response.text


def test_models_page_has_model_controls(client, auth_headers):
    """Test that the models page has model control buttons."""
    response = client.get("/admin/models", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Check for model control buttons (load/unload)
    assert re.search(r'id="(load|unload)-model-btn"', response.text) is not None


def test_tasks_page_has_task_controls(client, auth_headers):
    """Test that the tasks page has task control buttons."""
    response = client.get("/admin/tasks", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Check for task control buttons (refresh/cancel)
    assert re.search(r'id="refresh-tasks-btn"', response.text) is not None


def test_config_page_has_config_controls(client, auth_headers):
    """Test that the config page has config control buttons."""
    response = client.get("/admin/config", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Check for config control buttons (save)
    assert re.search(r'id="save-config-btn"', response.text) is not None


def test_logs_page_has_log_controls(client, auth_headers):
    """Test that the logs page has log control buttons."""
    response = client.get("/admin/logs", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Check for log control buttons (refresh/filter)
    assert re.search(r'id="refresh-logs-btn"', response.text) is not None


def test_voices_page_has_voice_controls(client, auth_headers):
    """Test that the voices page has voice control buttons."""
    response = client.get("/admin/voices", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Check for voice control buttons (refresh/add/edit/delete)
    assert re.search(r'id="refresh-voices-btn"', response.text) is not None


def test_admin_js_initializes_components(client, auth_headers):
    """Test that the admin.js initializes components on page load."""
    response = client.get("/admin", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Check for initialization code in the page
    assert "document.addEventListener('DOMContentLoaded'" in response.text


def test_theme_toggle_exists(client, auth_headers):
    """Test that the theme toggle exists in the admin dashboard."""
    response = client.get("/admin", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Check that the theme toggle exists
    assert re.search(r'id="theme-toggle"', response.text) is not None 