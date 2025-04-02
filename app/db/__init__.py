"""
Database initialization for EchoForge.
"""

import logging
from app.db.base import Base, engine

logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database."""
    try:
        # Create all tables in the database
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
