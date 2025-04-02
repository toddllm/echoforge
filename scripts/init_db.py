#!/usr/bin/env python3
"""
Database initialization script for EchoForge.

This script initializes the database and runs migrations.
"""

import os
import sys
import argparse
import logging
import subprocess
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import EchoForge modules
from app.core.env_loader import load_env_files
from app.db import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("echoforge.db_init")

def run_migrations():
    """Run database migrations using Alembic."""
    logger.info("Running database migrations with Alembic")
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=Path(__file__).parent.parent,
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"Migration output: {result.stdout}")
        if result.stderr:
            logger.warning(f"Migration warnings: {result.stderr}")
        logger.info("Database migrations completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run migrations: {e}")
        if e.stdout:
            logger.error(f"Migration stdout: {e.stdout}")
        if e.stderr:
            logger.error(f"Migration stderr: {e.stderr}")
        return False

def create_admin_user(username, email, password):
    """Create an admin user in the database."""
    logger.info(f"Creating admin user with username: {username}")
    
    # Import here to avoid circular imports
    from sqlalchemy.orm import Session
    from app.db.base import SessionLocal
    from app.services.user_service import UserCreate, create_user
    from app.db.models import User
    
    # Create session
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.is_admin:
                logger.info(f"Admin user {username} already exists")
                return True
            else:
                # Upgrade to admin
                existing_user.is_admin = True
                db.commit()
                logger.info(f"Upgraded user {username} to admin")
                return True
        
        # Create new admin user
        user_data = UserCreate(
            email=email,
            username=username,
            password=password,
            first_name="Admin",
            last_name="User"
        )
        
        user = create_user(db, user_data)
        
        # Set admin flag
        user.is_admin = True
        db.commit()
        
        logger.info(f"Admin user {username} created successfully")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create admin user: {e}")
        return False
    finally:
        db.close()

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Initialize EchoForge database")
    parser.add_argument("--migrations", action="store_true", help="Run database migrations")
    parser.add_argument("--create-admin", action="store_true", help="Create admin user")
    parser.add_argument("--admin-username", default="admin", help="Admin username")
    parser.add_argument("--admin-email", default="admin@example.com", help="Admin email")
    parser.add_argument("--admin-password", default="changeme123", help="Admin password")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_env_files()
    
    # Initialize database tables
    logger.info("Initializing database tables")
    try:
        init_db()
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        sys.exit(1)
    
    # Run migrations if requested
    if args.migrations:
        success = run_migrations()
        if not success:
            sys.exit(1)
    
    # Create admin user if requested
    if args.create_admin:
        success = create_admin_user(
            username=args.admin_username,
            email=args.admin_email,
            password=args.admin_password
        )
        if not success:
            sys.exit(1)
    
    logger.info("Database initialization completed successfully")

if __name__ == "__main__":
    main()
