"""
EchoForge Test Mode Configuration

This module provides centralized handling of test mode settings and behaviors.
Test mode is used for automated testing and development environments where
full authentication may be unnecessary or impractical.
"""

import os
import logging
from typing import Dict, Any

# Setup logging
logger = logging.getLogger(__name__)

class TestMode:
    """
    Test mode configuration and utilities.
    
    This class centralizes all test mode functionality and provides
    helper methods to determine if test mode is active and what behavior
    should be applied.
    """
    
    def __init__(self):
        """Initialize test mode configuration."""
        self._is_active = False
        self._test_user = "test_user"
        self._test_admin = True
        self.start_time = None
        self._refresh()
    
    def _refresh(self):
        """Read environment variables to determine test mode status."""
        # Check environment variable
        env_test_mode = os.environ.get("ECHOFORGE_TEST") == "true"
        if env_test_mode and not self._is_active:
            import datetime
            self.start_time = datetime.datetime.now().isoformat()
            logger.info(f"🧪 EchoForge running in TEST MODE (activated at {self.start_time})")
        self._is_active = env_test_mode
    
    @property
    def is_active(self) -> bool:
        """Check if test mode is currently active."""
        return self._is_active
    
    @property
    def test_user(self) -> str:
        """Get the test user identifier."""
        return self._test_user
    
    @property
    def test_admin(self) -> bool:
        """Check if the test user has admin privileges."""
        return self._test_admin
    
    def set_active(self, active: bool = True):
        """Explicitly set test mode active state.
        
        Args:
            active: Whether test mode should be active
        """
        self._is_active = active
        if self._is_active:
            import datetime
            self.start_time = datetime.datetime.now().isoformat()
            logger.info(f"🧪 Test mode explicitly activated at {self.start_time}")
        else:
            logger.info("Test mode explicitly deactivated")
            
    def force_refresh(self):
        """Force refresh the test mode status from environment variables.
        
        This is useful when the environment might have changed after initialization,
        such as when environment variables are set in a parent process.
        """
        previous_state = self._is_active
        self._refresh()
        if previous_state != self._is_active:
            if self._is_active:
                logger.info("🧪 Test mode activated through force refresh")
            else:
                logger.info("⚠️ Test mode deactivated through force refresh")
        return self._is_active
    
    def create_test_session_data(self) -> Dict[str, Any]:
        """
        Create test session data for authenticated sessions.
        
        Returns:
            Dict containing session data for test mode.
        """
        return {
            "user_id": self.test_user,
            "is_authenticated": True,
            "is_admin": self.test_admin,
            "test_mode": True
        }
    
    def log_bypass(self, feature: str):
        """Log when a security feature is bypassed in test mode."""
        if self.is_active:
            logger.debug(f"Test mode - bypassing {feature}")


# Create a singleton instance
test_mode = TestMode()
