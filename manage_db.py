#!/usr/bin/env python3
"""
Database management script for the Telegram bot.
Provides easy commands for backup, restore, and database operations.
"""

import os
import sys
import glob
from datetime import datetime

def list_backups():
    """List all available backup files"""
    backup_files = glob.glob('backup_bot_data_*.db')
    
    if not backup_files:
        print("📋 No backup files found")
        return
    
    print("📋 Available backup files:")
    for i, backup in enumerate(sorted(backup_files, key=os.path.getctime, reverse=True), 1):
        size = os.path.getsize(backup)
        ctime = datetime.fromtimestamp(os.path.getctime(backup))
        print(f"  {i}. {backup} ({size:,} bytes, {ctime.strftime('%Y-%m-%d %H:%M:%S')})")

def backup_current():
    """Backup the current database"""
    if not os.path.exists('bot_data.db'):
        print("❌ No current database to backup")
        return False
    
    from backup_db import backup_database
    return backup_database()

def restore_from_backup(backup_index=None):
    """Restore database from a specific backup"""
    backup_files = glob.glob('backup_bot_data_*.db')
    
    if not backup_files:
        print("❌ No backup files found")
        return False
    
    # Sort by creation time (newest first)
    sorted_backups = sorted(backup_files, key=os.path.getctime, reverse=True)
    
    if backup_index is None:
        # Use the most recent backup
        selected_backup = sorted_backups[0]
    else:
        try:
            selected_backup = sorted_backups[backup_index - 1]
        except IndexError:
            print(f"❌ Invalid backup index: {backup_index}")
            return False
    
    print(f"🔄 Restoring from: {selected_backup}")
    
    # Create backup of current database if it exists
    if os.path.exists('bot_data.db'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        current_backup = f'current_db_backup_{timestamp}.db'
        os.rename('bot_data.db', current_backup)
        print(f"📋 Current database backed up as: {current_backup}")
    
    # Restore from selected backup
    import shutil
    shutil.copy2(selected_backup, 'bot_data.db')
    
    file_size = os.path.getsize('bot_data.db')
    print(f"✅ Database restored successfully ({file_size:,} bytes)")
    return True

def show_help():
    """Show help information"""
    print("""
🔧 Database Management Script

Usage: python manage_db.py [command] [options]

Commands:
  list                    List all available backup files
  backup                  Create a backup of the current database
  restore [index]         Restore database from backup (default: most recent)
  help                    Show this help message

Examples:
  python manage_db.py list
  python manage_db.py backup
  python manage_db.py restore
  python manage_db.py restore 2
""")

def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_backups()
    elif command == 'backup':
        backup_current()
    elif command == 'restore':
        backup_index = int(sys.argv[2]) if len(sys.argv) > 2 else None
        restore_from_backup(backup_index)
    elif command == 'help':
        show_help()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main() 