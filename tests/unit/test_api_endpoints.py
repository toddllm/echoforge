"""
Unit tests for API endpoints.
"""

import os
import json
import unittest
import asyncio
from unittest.mock import patch, MagicMock

from app.api.router import health_check, system_diagnostic
from app.core import config


class TestAPIEndpoints(unittest.TestCase):
    """Test suite for API endpoints."""

    def setUp(self):
        """Set up test environment."""
        # Set test mode environment variable
        os.environ["ECHOFORGE_TEST"] = "true"

    def tearDown(self):
        """Clean up after tests."""
        # Unset test mode environment variable
        if "ECHOFORGE_TEST" in os.environ:
            del os.environ["ECHOFORGE_TEST"]

    def test_health_check(self):
        """Test health check endpoint."""
        # Call the endpoint function directly using asyncio
        response = asyncio.run(health_check())
        
        # Verify response
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["version"], config.APP_VERSION)

    @patch("app.api.router.platform")
    @patch("app.api.router.psutil")
    @patch("app.api.router.torch")
    def test_diagnostic_endpoint(self, mock_torch, mock_psutil, mock_platform):
        """Test diagnostic endpoint."""
        # Mock platform data
        mock_platform.system.return_value = "Linux"
        mock_platform.version.return_value = "5.10.0"
        mock_platform.python_version.return_value = "3.9.0"
        
        # Mock psutil data
        mock_memory = MagicMock()
        mock_memory.total = 16 * 1024 * 1024 * 1024  # 16 GB
        mock_memory.available = 8 * 1024 * 1024 * 1024  # 8 GB
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_count.side_effect = lambda logical: 16 if logical else 8
        
        # Mock torch data
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.version.cuda = "11.1"
        
        # Mock device properties
        mock_device_props = MagicMock()
        mock_device_props.name = "NVIDIA GeForce RTX 3080"
        mock_device_props.total_memory = 10 * 1024 * 1024 * 1024  # 10 GB
        mock_device_props.major = 8
        mock_device_props.minor = 6
        mock_torch.cuda.get_device_properties.return_value = mock_device_props
        
        # Call the endpoint function directly using asyncio
        response = asyncio.run(system_diagnostic())
        
        # Verify response
        self.assertEqual(response["system"]["os"], "Linux")
        self.assertEqual(response["system"]["os_version"], "5.10.0")
        self.assertEqual(response["system"]["python_version"], "3.9.0")
        self.assertEqual(response["system"]["cpu_count"], 8)
        self.assertEqual(response["system"]["logical_cpu_count"], 16)
        self.assertEqual(response["system"]["memory_total_gb"], 16.0)
        self.assertEqual(response["system"]["memory_available_gb"], 8.0)
        
        # Check CUDA info
        self.assertTrue(response["cuda"]["cuda_available"])
        self.assertEqual(response["cuda"]["cuda_device_count"], 1)
        self.assertEqual(response["cuda"]["cuda_version"], "11.1")
        self.assertEqual(len(response["cuda"]["devices"]), 1)
        self.assertEqual(response["cuda"]["devices"][0]["name"], "NVIDIA GeForce RTX 3080")
        self.assertEqual(response["cuda"]["devices"][0]["total_memory_gb"], 10.0)
        self.assertEqual(response["cuda"]["devices"][0]["major"], 8)
        self.assertEqual(response["cuda"]["devices"][0]["minor"], 6)

    @patch("app.api.router.torch.cuda.is_available")
    def test_diagnostic_endpoint_no_cuda(self, mock_cuda_available):
        """Test diagnostic endpoint when CUDA is not available."""
        # Mock CUDA availability
        mock_cuda_available.return_value = False
        
        # Call the endpoint function directly using asyncio
        response = asyncio.run(system_diagnostic())
        
        # Verify response
        self.assertFalse(response["cuda"]["cuda_available"])
        self.assertEqual(response["cuda"]["cuda_device_count"], 0)
        self.assertNotIn("devices", response["cuda"])

    @patch("app.api.router.voice_generator")
    def test_diagnostic_endpoint_with_model(self, mock_voice_generator):
        """Test diagnostic endpoint with model information."""
        # Mock voice generator
        mock_voice_generator.model = MagicMock()
        mock_voice_generator.model_path = "/path/to/model"
        mock_voice_generator.output_dir = "/path/to/output"
        mock_voice_generator.list_available_voices.return_value = [
            {"speaker_id": 1, "name": "Voice 1"},
            {"speaker_id": 2, "name": "Voice 2"}
        ]
        
        # Call the endpoint function directly using asyncio
        response = asyncio.run(system_diagnostic())
        
        # Verify response
        self.assertTrue(response["model"]["model_loaded"])
        self.assertEqual(response["model"]["model_path"], "/path/to/model")
        self.assertEqual(response["model"]["output_dir"], "/path/to/output")
        self.assertEqual(response["model"]["available_voices"], 2)

    @patch("app.api.router.task_manager")
    def test_diagnostic_endpoint_with_tasks(self, mock_task_manager):
        """Test diagnostic endpoint with task information."""
        # Mock task manager
        mock_task_manager.count_active_tasks.return_value = 2
        mock_task_manager.count_completed_tasks.return_value = 5
        mock_task_manager.count_failed_tasks.return_value = 1
        
        # Call the endpoint function directly using asyncio
        response = asyncio.run(system_diagnostic())
        
        # Verify response
        self.assertEqual(response["tasks"]["active_tasks"], 2)
        self.assertEqual(response["tasks"]["completed_tasks"], 5)
        self.assertEqual(response["tasks"]["failed_tasks"], 1)


if __name__ == "__main__":
    unittest.main() 