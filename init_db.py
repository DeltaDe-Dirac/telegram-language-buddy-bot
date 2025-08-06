#!/usr/bin/env python3
"""
Database initialization script for Heroku deployment.
Run this after deploying to create the database tables.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.database import DatabaseManager, Base

def init_database():
    """Initialize the database tables"""
    try:
        db = DatabaseManager()
        print("✅ Database initialized successfully")
        print(f"Database URL: {db.engine.url}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False

if __name__ == "__main__":
    print("Initializing database...")
    success = init_database()
    sys.exit(0 if success else 1) 