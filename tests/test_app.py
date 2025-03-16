"""
Test the main application.
"""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint(client):
    """Test the health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "ok"


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"] 