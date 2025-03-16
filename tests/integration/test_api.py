"""
Integration tests for the API endpoints.
"""

import os
import uuid
import json
import time
from unittest import mock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.voice_generator import VoiceGenerator


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_voice_generator():
    """Create a mock for the voice generator."""
    with mock.patch('app.api.routes.voice_generator') as mock_gen:
        # Configure the mock to provide necessary functionality
        mock_gen.output_dir = os.path.join(os.path.dirname(__file__), 'outputs')
        
        # Create output directory if it doesn't exist
        os.makedirs(mock_gen.output_dir, exist_ok=True)
        
        yield mock_gen


@pytest.fixture
def mock_task_manager():
    """Create a mock for the task manager."""
    with mock.patch('app.api.routes.task_manager') as mock_tm:
        tasks = {}
        
        # Mock task_manager.register_task
        def register_task(task_id, data):
            tasks[task_id] = {
                "status": "pending",
                "progress": 0.0,
                "created_at": time.time(),
                **data
            }
            return True
        
        # Mock task_manager.update_task
        def update_task(task_id, data):
            if task_id not in tasks:
                return False
            tasks[task_id].update(data)
            if data.get('status') in ['completed', 'failed'] and 'completed_at' not in tasks[task_id]:
                tasks[task_id]['completed_at'] = time.time()
            return True
        
        # Mock task_manager.get_task
        def get_task(task_id):
            return tasks.get(task_id)
        
        # Set up the mock methods
        mock_tm.register_task.side_effect = register_task
        mock_tm.update_task.side_effect = update_task
        mock_tm.get_task.side_effect = get_task
        
        yield mock_tm


def test_list_voices(client, mock_voice_generator):
    """Test the /voices endpoint."""
    # Set up mock to return test voices
    mock_voice_generator.list_available_voices.return_value = [
        {
            "speaker_id": 1,
            "name": "Test Voice 1",
            "gender": "male",
            "description": "Test description 1",
            "sample_url": "/static/samples/test1.wav"
        },
        {
            "speaker_id": 2,
            "name": "Test Voice 2",
            "gender": "female",
            "description": "Test description 2",
            "sample_url": "/static/samples/test2.wav"
        }
    ]
    
    # Make the request
    response = client.get("/api/v1/voices")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["speaker_id"] == 1
    assert data[0]["name"] == "Test Voice 1"
    assert data[1]["speaker_id"] == 2
    assert data[1]["name"] == "Test Voice 2"
    
    # Verify mock was called
    mock_voice_generator.list_available_voices.assert_called_once()


def test_list_voices_error(client, mock_voice_generator):
    """Test error handling in the /voices endpoint."""
    # Set up mock to raise an exception
    mock_voice_generator.list_available_voices.side_effect = RuntimeError("Test error")
    
    # Make the request
    response = client.get("/api/v1/voices")
    
    # Verify the response
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "Test error" in data["detail"]


def test_generate_voice(client, mock_voice_generator, mock_task_manager):
    """Test the /generate endpoint."""
    # Make the request
    response = client.post(
        "/api/v1/generate",
        json={
            "text": "Hello, this is a test.",
            "speaker_id": 1,
            "options": {
                "temperature": 0.5,
                "top_k": 80,
                "device": "cpu",
                "style": "short"
            }
        }
    )
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    
    assert "task_id" in data
    assert "status" in data
    assert data["status"] == "pending"
    
    # Verify mocks were called correctly
    mock_task_manager.register_task.assert_called_once()
    args, kwargs = mock_task_manager.register_task.call_args
    task_id = args[0]
    task_data = args[1]
    
    assert "text" in task_data
    assert "speaker_id" in task_data
    assert "temperature" in task_data
    assert "top_k" in task_data
    assert "device" in task_data
    assert "style" in task_data
    assert "created_at" in task_data
    
    assert task_data["text"] == "Hello, this is a test."
    assert task_data["speaker_id"] == 1
    assert task_data["temperature"] == 0.5
    assert task_data["top_k"] == 80
    assert task_data["device"] == "cpu"
    assert task_data["style"] == "short"


def test_generate_voice_empty_text(client, mock_voice_generator, mock_task_manager):
    """Test the /generate endpoint with empty text."""
    # Make the request with empty text
    response = client.post(
        "/api/v1/generate",
        json={
            "text": "",
            "speaker_id": 1
        }
    )
    
    # Verify the response
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Text cannot be empty" in data["detail"]
    
    # Verify mocks were not called
    mock_task_manager.register_task.assert_not_called()


def test_task_status_completed(client, mock_task_manager):
    """Test the /tasks/{task_id} endpoint for a completed task."""
    # Create a task
    task_id = str(uuid.uuid4())
    task_data = {
        "text": "Test text",
        "speaker_id": 1,
        "temperature": 0.5,
        "top_k": 80,
        "device": "cpu",
        "style": "short",
        "created_at": time.time()
    }
    mock_task_manager.register_task(task_id, task_data)
    
    # Update the task to completed
    output_path = "/path/to/output/voice_1_12345678.wav"
    mock_task_manager.update_task(task_id, {
        "status": "completed",
        "progress": 100.0,
        "output_path": output_path
    })
    
    # Make the request
    response = client.get(f"/api/v1/tasks/{task_id}")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    
    assert "task_id" in data
    assert "status" in data
    assert "progress" in data
    assert "result_url" in data
    assert "error" in data
    
    assert data["task_id"] == task_id
    assert data["status"] == "completed"
    assert data["progress"] == 100.0
    assert data["result_url"] == "/api/v1/voices/voice_1_12345678.wav"
    assert data["error"] is None


def test_task_status_failed(client, mock_task_manager):
    """Test the /tasks/{task_id} endpoint for a failed task."""
    # Create a task
    task_id = str(uuid.uuid4())
    task_data = {
        "text": "Test text",
        "speaker_id": 1,
        "temperature": 0.5,
        "top_k": 80,
        "device": "cpu",
        "style": "short",
        "created_at": time.time()
    }
    mock_task_manager.register_task(task_id, task_data)
    
    # Update the task to failed
    mock_task_manager.update_task(task_id, {
        "status": "failed",
        "progress": 100.0,
        "error": "Test error message"
    })
    
    # Make the request
    response = client.get(f"/api/v1/tasks/{task_id}")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    
    assert data["task_id"] == task_id
    assert data["status"] == "failed"
    assert data["progress"] == 100.0
    assert data["result_url"] is None
    assert data["error"] == "Test error message"


def test_task_status_not_found(client, mock_task_manager):
    """Test the /tasks/{task_id} endpoint for a non-existent task."""
    # Make the request with a random task_id
    task_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/tasks/{task_id}")
    
    # Verify the response
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert f"Task {task_id} not found" in data["detail"]


def test_get_voice_file(client, mock_voice_generator):
    """Test the /voices/{filename} endpoint."""
    # Create a temporary voice file
    filename = "test_voice.wav"
    file_path = os.path.join(mock_voice_generator.output_dir, filename)
    
    # Create an empty file
    with open(file_path, 'wb') as f:
        f.write(b'test audio data')
    
    try:
        # Setup mock to return the path
        mock_voice_generator.output_dir = os.path.dirname(file_path)
        
        # Make the request
        response = client.get(f"/api/v1/voices/{filename}")
        
        # Verify the response
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"
        assert response.headers["content-disposition"] == f'attachment; filename="{filename}"'
        assert response.content == b'test audio data'
        
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)


def test_get_voice_file_not_found(client, mock_voice_generator):
    """Test the /voices/{filename} endpoint for a non-existent file."""
    # Set up a path that doesn't exist
    mock_voice_generator.output_dir = "/path/that/doesnt/exist"
    
    # Make the request with a random filename
    filename = f"nonexistent_{uuid.uuid4()}.wav"
    response = client.get(f"/api/v1/voices/{filename}")
    
    # Verify the response
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert f"Voice file {filename} not found" in data["detail"]


def test_generate_task_function(mock_voice_generator, mock_task_manager):
    """Test the _generate_voice_task function."""
    # Import the function directly
    from app.api.routes import _generate_voice_task
    
    # Setup voice_generator.generate to return a valid path
    output_path = "/path/to/output/voice_1_12345678.wav"
    mock_voice_generator.generate.return_value = (output_path, None)
    
    # Call the function
    task_id = str(uuid.uuid4())
    text = "Test text"
    speaker_id = 1
    temperature = 0.5
    top_k = 80
    device = "cpu"
    style = "short"
    
    # Since this is an async function, we need to create and run a coroutine
    import asyncio
    
    async def run_task():
        await _generate_voice_task(
            task_id=task_id,
            text=text,
            speaker_id=speaker_id,
            temperature=temperature,
            top_k=top_k,
            device=device,
            style=style
        )
    
    # Run the coroutine
    asyncio.run(run_task())
    
    # Verify mocks were called correctly
    mock_task_manager.update_task.assert_called()
    mock_voice_generator.generate.assert_called_with(
        text=text,
        speaker_id=speaker_id,
        temperature=temperature,
        top_k=top_k,
        style=style,
        device=device
    )
    
    # First call should be to update to processing
    first_call_args = mock_task_manager.update_task.call_args_list[0][0]
    assert first_call_args[0] == task_id
    assert first_call_args[1]["status"] == "processing"
    
    # Last call should be to update to completed
    last_call_args = mock_task_manager.update_task.call_args_list[-1][0]
    assert last_call_args[0] == task_id
    assert last_call_args[1]["status"] == "completed"
    assert last_call_args[1]["output_path"] == output_path
    assert last_call_args[1]["progress"] == 100.0


def test_generate_task_function_error(mock_voice_generator, mock_task_manager):
    """Test the _generate_voice_task function when generation fails."""
    # Import the function directly
    from app.api.routes import _generate_voice_task
    
    # Setup voice_generator.generate to return an error
    error_message = "Test error message"
    mock_voice_generator.generate.return_value = (None, error_message)
    
    # Call the function
    task_id = str(uuid.uuid4())
    
    # Since this is an async function, we need to create and run a coroutine
    import asyncio
    
    async def run_task():
        await _generate_voice_task(
            task_id=task_id,
            text="Test text",
            speaker_id=1,
            temperature=0.5,
            top_k=80,
            device="cpu",
            style="short"
        )
    
    # Run the coroutine
    asyncio.run(run_task())
    
    # Verify mocks were called correctly
    # Last call should be to update to failed
    last_call_args = mock_task_manager.update_task.call_args_list[-1][0]
    assert last_call_args[0] == task_id
    assert last_call_args[1]["status"] == "failed"
    assert last_call_args[1]["error"] == error_message
    assert last_call_args[1]["progress"] == 100.0 