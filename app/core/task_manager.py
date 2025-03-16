"""
Task Manager for EchoForge.

This module provides a task management system for tracking long-running background tasks.
"""

import logging
import time
import uuid
import threading
from typing import Dict, List, Any, Optional, TypedDict, Union

from app.core import config

# Setup logging
logger = logging.getLogger(__name__)


class TaskData(TypedDict, total=False):
    """Type definition for task data."""
    task_id: str
    task_type: str
    status: str
    created_at: float
    updated_at: float
    result: Optional[Dict[str, Any]]
    error: Optional[str]


class TaskManager:
    """
    Task Manager for handling background tasks.
    
    This class manages the creation, updating, retrieval, and cleanup of
    background tasks in the EchoForge application.
    """
    
    def __init__(self, max_tasks: int = config.MAX_TASKS) -> None:
        """
        Initialize the task manager.
        
        Args:
            max_tasks: Maximum number of tasks to store
        """
        self.tasks: Dict[str, TaskData] = {}
        self.max_tasks = max_tasks
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        
        logger.info("TaskManager initialized with max_tasks=%d", max_tasks)
    
    def register_task(self, task_type: str) -> str:
        """
        Register a new task.
        
        Args:
            task_type: The type of task being registered
            
        Returns:
            The unique task ID
        """
        with self.lock:
            # Clean up old tasks if we're at the limit
            if len(self.tasks) >= self.max_tasks:
                self._cleanup_old_tasks()
            
            # Generate a unique ID
            task_id = str(uuid.uuid4())
            
            # Create the task record
            current_time = time.time()
            self.tasks[task_id] = {
                "task_id": task_id,
                "task_type": task_type,
                "status": "pending",
                "created_at": current_time,
                "updated_at": current_time,
                "result": None,
                "error": None
            }
            
            logger.info("Registered new %s task with ID: %s", task_type, task_id)
            return task_id
    
    def update_task(self, task_id: str, status: str = None, 
                   result: Dict[str, Any] = None, error: str = None) -> bool:
        """
        Update a task's status, result, or error message.
        
        Args:
            task_id: The unique ID of the task
            status: New status value (pending, processing, completed, error)
            result: Task result data (for completed tasks)
            error: Error message (for failed tasks)
            
        Returns:
            True if the task was updated, False if the task wasn't found
        """
        with self.lock:
            if task_id not in self.tasks:
                logger.warning("Attempted to update non-existent task: %s", task_id)
                return False
            
            # Update the task data
            task = self.tasks[task_id]
            
            if status:
                task["status"] = status
            
            if result is not None:
                task["result"] = result
            
            if error is not None:
                task["error"] = error
            
            # Update the timestamp
            task["updated_at"] = time.time()
            
            logger.debug("Updated task %s status to %s", task_id, status or task["status"])
            return True
    
    def get_task(self, task_id: str) -> Optional[TaskData]:
        """
        Get task data by ID.
        
        Args:
            task_id: The unique ID of the task
            
        Returns:
            Task data dictionary or None if not found
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                logger.debug("Task %s not found", task_id)
            return task
    
    def list_tasks(self, status: str = None, limit: int = 10) -> List[TaskData]:
        """
        List tasks, optionally filtered by status.
        
        Args:
            status: Filter by task status
            limit: Maximum number of tasks to return
            
        Returns:
            List of task data dictionaries
        """
        with self.lock:
            # Filter tasks by status if specified
            if status:
                filtered_tasks = [task for task in self.tasks.values() 
                                 if task["status"] == status]
            else:
                filtered_tasks = list(self.tasks.values())
            
            # Sort by updated_at (newest first)
            sorted_tasks = sorted(filtered_tasks, 
                                 key=lambda t: t["updated_at"], 
                                 reverse=True)
            
            # Limit the number of results
            return sorted_tasks[:limit]
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task by ID.
        
        Args:
            task_id: The unique ID of the task
            
        Returns:
            True if the task was deleted, False if not found
        """
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                logger.debug("Deleted task %s", task_id)
                return True
            else:
                logger.warning("Attempted to delete non-existent task: %s", task_id)
                return False
    
    def _cleanup_old_tasks(self, keep_newest: int = config.TASK_CLEANUP_KEEP_NEWEST) -> int:
        """
        Clean up old tasks when we hit the maximum.
        
        Args:
            keep_newest: Number of newest tasks to keep
            
        Returns:
            Number of tasks removed
        """
        # If we're not over the threshold, don't clean up
        if len(self.tasks) <= keep_newest:
            return 0
        
        # Sort tasks by updated_at time
        sorted_tasks = sorted(self.tasks.items(), 
                             key=lambda item: item[1]["updated_at"],
                             reverse=True)
        
        # Keep the newest N tasks
        tasks_to_keep = dict(sorted_tasks[:keep_newest])
        
        # Count how many we're removing
        removed_count = len(self.tasks) - len(tasks_to_keep)
        
        # Replace the tasks dictionary with the filtered one
        self.tasks = tasks_to_keep
        
        logger.info("Cleaned up %d old tasks", removed_count)
        return removed_count


# Create a singleton instance for application-wide use
task_manager = TaskManager() 