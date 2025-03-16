"""
Pytest configuration and fixtures.
"""

import os
import pytest
from unittest.mock import MagicMock
import tempfile
from fastapi.testclient import TestClient

from app.core.voice_generator import VoiceGenerator
from app.main import app


@pytest.fixture
def temp_audio_file():
    """Create a temporary audio file for testing."""
    fd, path = tempfile.mkstemp(suffix='.wav')
    try:
        os.close(fd)
        # Write some dummy data to the file
        with open(path, 'wb') as f:
            f.write(b'dummy audio data')
        yield path
    finally:
        os.unlink(path)


@pytest.fixture
def mock_voice_generator():
    """Return a mock voice generator that produces predictable output."""
    generator = MagicMock(spec=VoiceGenerator)
    generator.generate.return_value = b'mock audio data'
    return generator


@pytest.fixture
def test_db_connection():
    """Return a test database connection."""
    # This would normally set up a test database connection
    # For now, we'll just return a mock
    db = MagicMock()
    db.execute.return_value = None
    return db


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def test_env():
    """Set up test environment variables."""
    # Store original environment
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ["ECHOFORGE_TEST"] = "true"
    os.environ["OUTPUT_DIR"] = "/tmp/echoforge_test/voices"
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env) 