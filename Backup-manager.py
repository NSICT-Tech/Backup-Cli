#!/usr/bin/env python3
"""
Backup Checker App
Monitors last backup date and alerts user when backup is overdue (>3 days)
"""

import sqlite3
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
DB_PATH = os.path.expanduser("~/.backup_manager/backups.db")
LOG_PATH = os.path.expanduser("~/.backup_manager/checker.log")
ALERT_THRESHOLD_DAYS = 3

def setup_logging():
    """Configure logging to file and console"""
    log_dir = Path(LOG_PATH).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_PATH),
            logging.StreamHandler()
        ]
    )

def init_database():
    """Initialize database and tables if they don't exist"""
    try:
        db_dir = Path(DB_PATH).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create meta table for global settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        # Create backups table for history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                file_count INTEGER NOT NULL,
                source_path TEXT,
                backup_path TEXT
            )
        ''')
        
        # Create files table for tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE,
                file_size INTEGER NOT NULL,
                last_modified REAL NOT NULL,
                last_backup TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")
        return False

def get_last_backup_date():
    """Retrieve the last backup date from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Try to get from meta table first
        cursor.execute("SELECT value FROM meta WHERE key = 'last_backup_date'")
        result = cursor.fetchone()
        
        if result:
            conn.close()
            return datetime.fromisoformat(result[0])
        
        # If not in meta, check backups table for most recent backup
        cursor.execute("SELECT timestamp FROM backups ORDER BY timestamp DESC LIMIT 1")
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return datetime.fromisoformat(result[0])
        
        logging.warning("No backup history found in database")
        return None
        
    except sqlite3.Error as e:
        logging.error(f"Database error while retrieving last backup date: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error retrieving last backup date: {e}")
        return None

def check_backup_status():
    """Check if backup is overdue and alert user if necessary"""
    try:
        current_date = datetime.now()
        logging.info(f"Backup check initiated at {current_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        last_backup = get_last_backup_date()
        
        if last_backup is None:
            print("\n" + "="*60)
            print("⚠️  BACKUP ALERT!")
            print("="*60)
            print("No backup history found in the system.")
            print("Your data is important. Please run your first backup today!")
            print("Run: python3 backup_manager.py")
            print("="*60 + "\n")
            logging.warning("No backup found - First backup needed")
            return
        
        days_since_backup = (current_date - last_backup).days
        
        logging.info(f"Last backup was on {last_backup.strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info(f"Days since last backup: {days_since_backup}")
        
        if days_since_backup > ALERT_THRESHOLD_DAYS:
            print("\n" + "="*60)
            print("⚠️  BACKUP ALERT!")
            print("="*60)
            print(f"Last backup: {last_backup.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Days since backup: {days_since_backup}")
            print("Your data is important. Please back it up today!")
            print("Run: python3 backup_manager.py")
            print("="*60 + "\n")
            logging.warning(f"Backup overdue by {days_since_backup - ALERT_THRESHOLD_DAYS} days - Alert sent")
        else:
            print(f"\n✅ Backup status: OK")
            print(f"Last backup: {last_backup.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Next backup recommended: {(last_backup + timedelta(days=ALERT_THRESHOLD_DAYS)).strftime('%Y-%m-%d')}\n")
            logging.info("Backup is up to date - No alert needed")
            
    except Exception as e:
        logging.error(f"Error during backup status check: {e}")
        print(f"\n❌ Error checking backup status. Check log file: {LOG_PATH}\n")

def main():
    """Main entry point"""
    setup_logging()
    
    logging.info("="*60)
    logging.info("Backup Checker App Started")
    logging.info("="*60)
    
    # Initialize database if needed
    if not init_database():
        print(f"❌ Failed to initialize database. Check log: {LOG_PATH}")
        return 1
    
    # Check backup status
    check_backup_status()
    
    logging.info("Backup Checker App Completed")
    logging.info("="*60)
    
    return 0

if __name__ == "__main__":
    exit(main())
