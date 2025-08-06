#!/usr/bin/env python3
"""
Database backup script for Heroku deployment.
Run this before deploying to backup the current database.
"""

import os
import sys
import shutil
from datetime import datetime

def backup_database():
    """Backup the SQLite database"""
    try:
        # Check if database exists
        if not os.path.exists('bot_data.db'):
            print("❌ No database file found to backup")
            return False
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_bot_data_{timestamp}.db'
        
        # Copy database file
        shutil.copy2('bot_data.db', backup_filename)
        
        # Get file size
        file_size = os.path.getsize(backup_filename)
        
        print(f"✅ Database backed up: {backup_filename}")
        print(f"📊 Backup size: {file_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

if __name__ == "__main__":
    print("Creating database backup...")
    success = backup_database()
    sys.exit(0 if success else 1) 