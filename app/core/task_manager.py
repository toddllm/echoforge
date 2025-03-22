"""
Task Manager for EchoForge.

This module provides a task management system for tracking long-running background tasks.
"""

import logging
import time
import uuid
import threading
import queue
import traceback
from typing import Dict, List, Any, Optional, TypedDict, Union, Callable

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
        
        # Task processing infrastructure
        self.task_queue = queue.Queue()
        self.task_handlers: Dict[str, Callable] = {}
        self.worker_thread = None
        self.stop_event = threading.Event()
        
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
    
    def update_task(self, task_id: str, status: str = None, progress: float = None,
                   result: Dict[str, Any] = None, error: str = None, 
                   device_info: str = None, message: str = None) -> bool:
        """
        Update a task's status, result, or error message.
        
        Args:
            task_id: The unique ID of the task
            status: New status value (pending, processing, completed, error)
            progress: Task progress percentage (0-100)
            result: Task result data (for completed tasks)
            error: Error message (for failed tasks)
            device_info: Information about the device being used
            message: Additional status message
            
        Returns:
            True if the task was updated, False if the task wasn't found
        """
        with self.lock:
            if task_id not in self.tasks:
                logger.warning("Attempted to update non-existent task: %s", task_id)
                return False
            
            # Update the task record
            if status is not None:
                self.tasks[task_id]["status"] = status
            
            if progress is not None:
                self.tasks[task_id]["progress"] = progress
            
            if result is not None:
                self.tasks[task_id]["result"] = result
            
            if error is not None:
                self.tasks[task_id]["error"] = error
            
            if device_info is not None:
                self.tasks[task_id]["device_info"] = device_info
            
            if message is not None:
                self.tasks[task_id]["message"] = message
            
            # Update the timestamp
            self.tasks[task_id]["updated_at"] = time.time()
            
            logger.debug("Updated task %s: status=%s, progress=%s", 
                        task_id, status, progress)
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
    
    def count_active_tasks(self) -> int:
        """
        Count the number of active tasks (pending or processing).
        
        Returns:
            Number of active tasks
        """
        with self.lock:
            return sum(1 for task in self.tasks.values() 
                      if task["status"] in ["pending", "processing"])
    
    def count_completed_tasks(self) -> int:
        """
        Count the number of completed tasks.
        
        Returns:
            Number of completed tasks
        """
        with self.lock:
            return sum(1 for task in self.tasks.values() 
                      if task["status"] == "completed")
    
    def count_failed_tasks(self) -> int:
        """
        Count the number of failed tasks.
        
        Returns:
            Number of failed tasks
        """
        with self.lock:
            return sum(1 for task in self.tasks.values() 
                      if task["status"] in ["error", "failed"])
    
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


    def register_task_handler(self, task_type: str, handler_function: Callable) -> None:
        """
        Register a handler function for a specific task type.
        
        Args:
            task_type: Type of task this handler processes
            handler_function: Function to call when processing this task type
        """
        self.task_handlers[task_type] = handler_function
        logger.info(f"Registered handler for task type: {task_type}")
    
    def start_worker(self) -> None:
        """
        Start the worker thread to process tasks in the background.
        """
        if self.worker_thread is not None and self.worker_thread.is_alive():
            logger.warning("Worker thread is already running")
            return
            
        self.stop_event.clear()
        self.worker_thread = threading.Thread(
            target=self._process_tasks, 
            daemon=True,  # Make it a daemon so it doesn't block app shutdown
            name="TaskManagerWorker"
        )
        self.worker_thread.start()
        logger.info("Started task worker thread")
    
    def stop_worker(self) -> None:
        """
        Stop the worker thread.
        """
        if self.worker_thread is None or not self.worker_thread.is_alive():
            logger.warning("Worker thread is not running")
            return
            
        logger.info("Stopping task worker thread...")
        self.stop_event.set()
        self.worker_thread.join(timeout=5.0)  # Wait up to 5 seconds for thread to end
        if self.worker_thread.is_alive():
            logger.warning("Worker thread did not stop gracefully after timeout")
        else:
            logger.info("Worker thread stopped successfully")
    
    def enqueue_task(self, task_id: str) -> bool:
        """
        Add a task to the processing queue.
        
        Args:
            task_id: The ID of the task to process
            
        Returns:
            True if the task was queued, False otherwise
        """
        if not self.worker_thread or not self.worker_thread.is_alive():
            logger.warning("Worker thread is not running, starting it now")
            self.start_worker()
            
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                logger.warning(f"Cannot enqueue non-existent task: {task_id}")
                return False
                
            task_type = task.get("task_type")
            if task_type not in self.task_handlers:
                logger.error(f"No handler registered for task type: {task_type}")
                self.update_task(
                    task_id, 
                    status="failed", 
                    error=f"No handler available for task type: {task_type}"
                )
                return False
            
            try:
                self.task_queue.put(task_id, block=False)
                self.update_task(task_id, status="queued", message="Task queued for processing")
                logger.info(f"Enqueued task {task_id} for processing")
                return True
            except queue.Full:
                logger.error(f"Task queue is full, couldn't enqueue task {task_id}")
                self.update_task(
                    task_id,
                    status="failed",
                    error="Task queue is full, try again later"
                )
                return False
    
    def _process_tasks(self) -> None:
        """
        Worker thread function that processes tasks from the queue.
        """
        logger.info("Task worker thread started")
        while not self.stop_event.is_set():
            try:
                # Try to get a task, but don't block indefinitely
                try:
                    task_id = self.task_queue.get(block=True, timeout=1.0)
                except queue.Empty:
                    # No task available, just continue the loop
                    continue
                    
                logger.info(f"Processing task {task_id} from queue")
                
                with self.lock:
                    task = self.tasks.get(task_id)
                    if not task:
                        logger.warning(f"Task {task_id} not found in tasks dict")
                        self.task_queue.task_done()
                        continue
                        
                    task_type = task.get("task_type")
                    if task_type not in self.task_handlers:
                        logger.error(f"No handler for task type {task_type}")
                        self.update_task(
                            task_id,
                            status="failed",
                            error=f"No handler registered for task type: {task_type}"
                        )
                        self.task_queue.task_done()
                        continue
                    
                    self.update_task(task_id, status="processing", message="Task processing started")
                
                # Get the handler for this task type
                handler = self.task_handlers[task_type]
                
                # Run the handler
                try:
                    logger.info(f"Executing handler for task {task_id} (type: {task_type})")
                    handler(task_id, task)
                    logger.info(f"Handler for task {task_id} completed successfully")
                except Exception as e:
                    logger.error(f"Error processing task {task_id}: {str(e)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    self.update_task(
                        task_id, 
                        status="failed", 
                        error=f"Error during task processing: {str(e)}"
                    )
                finally:
                    self.task_queue.task_done()
                    
            except Exception as e:
                logger.error(f"Unexpected error in task worker: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Don't exit the loop, try to recover
                
        logger.info("Task worker thread exiting")

# Create a singleton instance for application-wide use
task_manager = TaskManager() 