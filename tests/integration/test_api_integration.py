import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestVoiceGenerationAPI:
    def test_generate_endpoint_returns_job_id(self, client):
        # Prepare test data
        request_data = {
            "text": "Hello, this is a test.",
            "profile_id": 1,
            "options": {
                "temperature": 0.7,
                "top_k": 50
            }
        }
        
        # Call the API
        response = client.post("/api/v1/voices/generate", json=request_data)
        
        # Assertions
        assert response.status_code == 200
        assert "job_id" in response.json()
        assert "status" in response.json()
        assert response.json()["status"] == "pending"
    
    def test_get_task_status_endpoint(self, client):
        # Assuming a job was created
        job_id = "test-job-id"  # In a real test, this would be from a previous request
        
        # Call the API
        response = client.get(f"/api/v1/tasks/{job_id}")
        
        # Assertions
        assert response.status_code == 200
        assert "status" in response.json()
        # Status could be pending, processing, completed, or failed
        assert response.json()["status"] in ["pending", "processing", "completed", "failed"] 