"""
Unit tests for the TaskManager class.
"""

import time
import uuid
import unittest
from unittest.mock import patch

from app.core.task_manager import TaskManager


class TestTaskManager(unittest.TestCase):
    """Test suite for TaskManager class."""

    def setUp(self):
        """Set up test case with a fresh TaskManager instance."""
        self.task_manager = TaskManager(max_tasks=10)

    def test_register_task(self):
        """Test registering a new task."""
        task_id = str(uuid.uuid4())
        task_data = {"text": "Test text", "speaker_id": 1}
        
        result = self.task_manager.register_task(task_id, task_data)
        self.assertTrue(result)
        
        # Check if task was registered correctly
        task = self.task_manager.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task["text"], "Test text")
        self.assertEqual(task["speaker_id"], 1)
        self.assertEqual(task["status"], "pending")
        self.assertEqual(task["progress"], 0.0)
        self.assertIn("created_at", task)

    def test_update_task(self):
        """Test updating an existing task."""
        # Create a task first
        task_id = str(uuid.uuid4())
        self.task_manager.register_task(task_id, {"text": "Original text"})
        
        # Update the task
        result = self.task_manager.update_task(task_id, {
            "status": "processing", 
            "progress": 50.0
        })
        self.assertTrue(result)
        
        # Check if task was updated correctly
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task["status"], "processing")
        self.assertEqual(task["progress"], 50.0)
        self.assertEqual(task["text"], "Original text")  # Original data preserved
        
        # Test updating non-existent task
        non_existent_task_id = str(uuid.uuid4())
        result = self.task_manager.update_task(non_existent_task_id, {})
        self.assertFalse(result)

    def test_completed_task_timestamp(self):
        """Test that completed tasks get a completion timestamp."""
        task_id = str(uuid.uuid4())
        self.task_manager.register_task(task_id, {"text": "Test text"})
        
        # Update task to completed
        self.task_manager.update_task(task_id, {"status": "completed"})
        
        # Check if completion timestamp was added
        task = self.task_manager.get_task(task_id)
        self.assertIn("completed_at", task)
        
        # Same for failed tasks
        task_id = str(uuid.uuid4())
        self.task_manager.register_task(task_id, {"text": "Test text"})
        self.task_manager.update_task(task_id, {"status": "failed", "error": "Test error"})
        task = self.task_manager.get_task(task_id)
        self.assertIn("completed_at", task)

    def test_get_task(self):
        """Test retrieving a task."""
        # Create a task
        task_id = str(uuid.uuid4())
        self.task_manager.register_task(task_id, {"text": "Test text"})
        
        # Get the task
        task = self.task_manager.get_task(task_id)
        self.assertIsNotNone(task)
        
        # Test getting non-existent task
        non_existent_task_id = str(uuid.uuid4())
        task = self.task_manager.get_task(non_existent_task_id)
        self.assertIsNone(task)

    def test_list_tasks(self):
        """Test listing tasks."""
        # Create multiple tasks with different statuses
        task_id1 = str(uuid.uuid4())
        task_id2 = str(uuid.uuid4())
        task_id3 = str(uuid.uuid4())
        
        self.task_manager.register_task(task_id1, {"text": "Test 1"})
        self.task_manager.register_task(task_id2, {"text": "Test 2"})
        self.task_manager.register_task(task_id3, {"text": "Test 3"})
        
        self.task_manager.update_task(task_id2, {"status": "processing"})
        self.task_manager.update_task(task_id3, {"status": "completed"})
        
        # List all tasks
        all_tasks = self.task_manager.list_tasks()
        self.assertEqual(len(all_tasks), 3)
        
        # List pending tasks
        pending_tasks = self.task_manager.list_tasks(status="pending")
        self.assertEqual(len(pending_tasks), 1)
        
        # List processing tasks
        processing_tasks = self.task_manager.list_tasks(status="processing")
        self.assertEqual(len(processing_tasks), 1)
        
        # List completed tasks
        completed_tasks = self.task_manager.list_tasks(status="completed")
        self.assertEqual(len(completed_tasks), 1)

    def test_delete_task(self):
        """Test deleting a task."""
        # Create a task
        task_id = str(uuid.uuid4())
        self.task_manager.register_task(task_id, {"text": "Test text"})
        
        # Delete the task
        result = self.task_manager.delete_task(task_id)
        self.assertTrue(result)
        
        # Check if task was deleted
        task = self.task_manager.get_task(task_id)
        self.assertIsNone(task)
        
        # Test deleting non-existent task
        result = self.task_manager.delete_task(task_id)
        self.assertFalse(result)

    def test_cleanup_old_tasks(self):
        """Test cleaning up old tasks."""
        # Create tasks with artificial created_at timestamps
        now = time.time()
        one_day_ago = now - (25 * 3600)  # 25 hours ago
        
        # Create old completed task
        old_task_id = str(uuid.uuid4())
        self.task_manager.register_task(old_task_id, {"text": "Old task"})
        self.task_manager.tasks[old_task_id]["created_at"] = one_day_ago
        self.task_manager.update_task(old_task_id, {"status": "completed"})
        self.task_manager.tasks[old_task_id]["completed_at"] = one_day_ago
        
        # Create recent task
        recent_task_id = str(uuid.uuid4())
        self.task_manager.register_task(recent_task_id, {"text": "Recent task"})
        
        # Create old but still pending task (shouldn't be cleaned up)
        old_pending_task_id = str(uuid.uuid4())
        self.task_manager.register_task(old_pending_task_id, {"text": "Old pending task"})
        self.task_manager.tasks[old_pending_task_id]["created_at"] = one_day_ago
        
        # Clean up old tasks
        deleted_count = self.task_manager._cleanup_old_tasks(max_age_hours=24)
        
        # Verify only old completed task was deleted
        self.assertEqual(deleted_count, 1)
        self.assertIsNone(self.task_manager.get_task(old_task_id))
        self.assertIsNotNone(self.task_manager.get_task(recent_task_id))
        self.assertIsNotNone(self.task_manager.get_task(old_pending_task_id))

    def test_max_tasks_limit(self):
        """Test that old tasks are cleaned up when max_tasks is reached."""
        # Create max_tasks + 1 tasks
        for i in range(11):  # Our TaskManager has max_tasks=10
            task_id = str(uuid.uuid4())
            self.task_manager.register_task(task_id, {"text": f"Task {i}"})
            
            # Mark older tasks as completed so they can be cleaned up
            if i < 5:
                self.task_manager.update_task(task_id, {"status": "completed"})
                # Set completed_at to a day ago
                self.task_manager.tasks[task_id]["completed_at"] = time.time() - (25 * 3600)
        
        # We should still have 10 or fewer tasks as the cleanup should have happened
        self.assertLessEqual(len(self.task_manager.tasks), 10)

    @patch('app.core.task_manager.logger')
    def test_logging(self, mock_logger):
        """Test that key actions are logged."""
        task_id = str(uuid.uuid4())
        
        # Test registration logging
        self.task_manager.register_task(task_id, {"text": "Test text"})
        mock_logger.debug.assert_called_with(f"Registered task {task_id}")
        
        # Test update logging
        mock_logger.debug.reset_mock()
        self.task_manager.update_task(task_id, {"status": "processing"})
        mock_logger.debug.assert_called()
        
        # Test deletion logging
        mock_logger.debug.reset_mock()
        self.task_manager.delete_task(task_id)
        mock_logger.debug.assert_called_with(f"Deleted task {task_id}")


if __name__ == '__main__':
    unittest.main() 