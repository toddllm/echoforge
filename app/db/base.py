"""
Database setup and connection handling for EchoForge.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core import config

# Get the database URL from environment or use SQLite by default
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    f"sqlite:///{os.path.join(config.ROOT_DIR, 'echoforge.db')}"
)

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={} if SQLALCHEMY_DATABASE_URL.startswith("postgresql") else {"check_same_thread": False}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency to get a database session
def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
