#!/usr/bin/env python3
"""
Database restore script for Heroku deployment.
Run this after deploying to restore the database from backup.
"""

import os
import sys
import glob
from datetime import datetime

def restore_database():
    """Restore the SQLite database from backup"""
    try:
        # Find the most recent backup file
        backup_files = glob.glob('backup_bot_data_*.db')
        
        if not backup_files:
            print("❌ No backup files found")
            return False
        
        # Get the most recent backup
        latest_backup = max(backup_files, key=os.path.getctime)
        
        # Check if current database exists
        if os.path.exists('bot_data.db'):
            # Create a backup of current database before overwriting
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            current_backup = f'current_db_backup_{timestamp}.db'
            os.rename('bot_data.db', current_backup)
            print(f"📋 Current database backed up as: {current_backup}")
        
        # Restore from backup
        import shutil
        shutil.copy2(latest_backup, 'bot_data.db')
        
        # Get file size
        file_size = os.path.getsize('bot_data.db')
        
        print(f"✅ Database restored from: {latest_backup}")
        print(f"📊 Restored size: {file_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False

if __name__ == "__main__":
    print("Restoring database from backup...")
    success = restore_database()
    sys.exit(0 if success else 1) 