#!/usr/bin/env python3
"""
Backup Manager App
Handles full, smart, and clean backups with history tracking
"""

import sqlite3
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

# Configuration
DB_PATH = os.path.expanduser("~/.backup_manager/backups.db")
LOG_PATH = os.path.expanduser("~/.backup_manager/manager.log")

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
    """Initialize database and tables"""
    try:
        db_dir = Path(DB_PATH).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
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
        logging.info("Database initialized")
        return True
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        return False

def update_last_backup_date(timestamp):
    """Update the last backup date in meta table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO meta (key, value) VALUES ('last_backup_date', ?)
        ''', (timestamp,))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Failed to update last backup date: {e}")

def get_file_info(file_path):
    """Get file size and modification time"""
    try:
        stat = os.stat(file_path)
        return stat.st_size, stat.st_mtime
    except Exception as e:
        logging.error(f"Failed to get file info for {file_path}: {e}")
        return None, None

def full_backup(source_dir, backup_dir):
    """Perform full backup - copy all files without removing anything"""
    print("\n" + "="*60)
    print("🔄 Starting Full Backup...")
    print("="*60)
    
    logging.info(f"Full backup started: {source_dir} -> {backup_dir}")
    
    try:
        source_path = Path(source_dir).resolve()
        backup_path = Path(backup_dir).resolve()
        
        if not source_path.exists():
            print(f"❌ Error: Source directory does not exist: {source_dir}")
            logging.error(f"Source directory not found: {source_dir}")
            return
        
        backup_path.mkdir(parents=True, exist_ok=True)
        
        files_copied = 0
        files_skipped = 0
        errors = 0
        
        # Walk through all files in source
        for root, dirs, files in os.walk(source_path):
            for filename in files:
                try:
                    src_file = Path(root) / filename
                    rel_path = src_file.relative_to(source_path)
                    dst_file = backup_path / rel_path
                    
                    # Create destination directory if needed
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(src_file, dst_file)
                    files_copied += 1
                    
                    # Update database
                    size, mtime = get_file_info(src_file)
                    if size is not None:
                        update_file_record(str(rel_path), size, mtime)
                    
                    if files_copied % 10 == 0:
                        print(f"  Copied: {files_copied} files...", end='\r')
                    
                except Exception as e:
                    errors += 1
                    logging.error(f"Failed to copy {src_file}: {e}")
        
        # Record backup in database
        timestamp = datetime.now().isoformat()
        record_backup("full", timestamp, files_copied, str(source_path), str(backup_path))
        update_last_backup_date(timestamp)
        
        print("\n" + "-"*60)
        print(f"✅ Full Backup Complete!")
        print(f"   Files copied: {files_copied}")
        print(f"   Errors: {errors}")
        print(f"   Backup location: {backup_path}")
        print("="*60 + "\n")
        
        logging.info(f"Full backup completed: {files_copied} files copied, {errors} errors")
        
    except Exception as e:
        print(f"\n❌ Backup failed: {e}")
        logging.error(f"Full backup failed: {e}")

def smart_backup(source_dir, backup_dir):
    """Smart backup - only copy new or changed files"""
    print("\n" + "="*60)
    print("🧠 Starting Smart Backup...")
    print("="*60)
    
    logging.info(f"Smart backup started: {source_dir} -> {backup_dir}")
    
    try:
        source_path = Path(source_dir).resolve()
        backup_path = Path(backup_dir).resolve()
        
        if not source_path.exists():
            print(f"❌ Error: Source directory does not exist: {source_dir}")
            logging.error(f"Source directory not found: {source_dir}")
            return
        
        backup_path.mkdir(parents=True, exist_ok=True)
        
        files_copied = 0
        files_skipped = 0
        errors = 0
        
        # Get database records for comparison
        file_records = get_all_file_records()
        
        for root, dirs, files in os.walk(source_path):
            for filename in files:
                try:
                    src_file = Path(root) / filename
                    rel_path = str(src_file.relative_to(source_path))
                    dst_file = backup_path / rel_path
                    
                    size, mtime = get_file_info(src_file)
                    if size is None:
                        continue
                    
                    # Check if file needs to be copied
                    needs_copy = False
                    
                    if rel_path not in file_records:
                        needs_copy = True  # New file
                    elif file_records[rel_path]['size'] != size:
                        needs_copy = True  # Size changed
                    elif not dst_file.exists():
                        needs_copy = True  # File missing in backup
                    
                    if needs_copy:
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, dst_file)
                        files_copied += 1
                        update_file_record(rel_path, size, mtime)
                        
                        if files_copied % 10 == 0:
                            print(f"  Copied: {files_copied} files...", end='\r')
                    else:
                        files_skipped += 1
                    
                except Exception as e:
                    errors += 1
                    logging.error(f"Failed to process {src_file}: {e}")
        
        timestamp = datetime.now().isoformat()
        record_backup("smart", timestamp, files_copied, str(source_path), str(backup_path))
        update_last_backup_date(timestamp)
        
        print("\n" + "-"*60)
        print(f"✅ Smart Backup Complete!")
        print(f"   New/Changed files: {files_copied}")
        print(f"   Unchanged files: {files_skipped}")
        print(f"   Errors: {errors}")
        print(f"   Backup location: {backup_path}")
        print("="*60 + "\n")
        
        logging.info(f"Smart backup completed: {files_copied} copied, {files_skipped} skipped, {errors} errors")
        
    except Exception as e:
        print(f"\n❌ Backup failed: {e}")
        logging.error(f"Smart backup failed: {e}")

def clean_backup(source_dir, backup_dir):
    """Remove files from backup that no longer exist in source"""
    print("\n" + "="*60)
    print("🧹 Starting Clean Backup...")
    print("="*60)
    
    logging.info(f"Clean backup started: {source_dir} -> {backup_dir}")
    
    try:
        source_path = Path(source_dir).resolve()
        backup_path = Path(backup_dir).resolve()
        
        if not backup_path.exists():
            print(f"❌ Error: Backup directory does not exist: {backup_dir}")
            logging.error(f"Backup directory not found: {backup_dir}")
            return
        
        files_removed = 0
        errors = 0
        
        # Build set of source files
        source_files = set()
        if source_path.exists():
            for root, dirs, files in os.walk(source_path):
                for filename in files:
                    src_file = Path(root) / filename
                    rel_path = str(src_file.relative_to(source_path))
                    source_files.add(rel_path)
        
        # Check backup files
        for root, dirs, files in os.walk(backup_path):
            for filename in files:
                try:
                    backup_file = Path(root) / filename
                    rel_path = str(backup_file.relative_to(backup_path))
                    
                    if rel_path not in source_files:
                        # File doesn't exist in source, remove from backup
                        backup_file.unlink()
                        files_removed += 1
                        remove_file_record(rel_path)
                        print(f"  Removed: {rel_path}")
                        logging.info(f"Removed orphaned file: {rel_path}")
                    
                except Exception as e:
                    errors += 1
                    logging.error(f"Failed to process {backup_file}: {e}")
        
        # Remove empty directories
        for root, dirs, files in os.walk(backup_path, topdown=False):
            for dirname in dirs:
                try:
                    dir_path = Path(root) / dirname
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        logging.info(f"Removed empty directory: {dir_path}")
                except Exception as e:
                    logging.error(f"Failed to remove directory {dir_path}: {e}")
        
        print("-"*60)
        print(f"✅ Clean Backup Complete!")
        print(f"   Files removed: {files_removed}")
        print(f"   Errors: {errors}")
        print("="*60 + "\n")
        
        logging.info(f"Clean backup completed: {files_removed} files removed, {errors} errors")
        
    except Exception as e:
        print(f"\n❌ Clean failed: {e}")
        logging.error(f"Clean backup failed: {e}")

def view_history():
    """Display backup history from database"""
    print("\n" + "="*60)
    print("📜 Backup History")
    print("="*60)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT backup_type, timestamp, file_count, source_path, backup_path 
            FROM backups 
            ORDER BY timestamp DESC
        ''')
        
        backups = cursor.fetchall()
        conn.close()
        
        if not backups:
            print("No backup history found.")
            print("="*60 + "\n")
            return
        
        for i, (btype, timestamp, count, src, dst) in enumerate(backups, 1):
            dt = datetime.fromisoformat(timestamp)
            print(f"\n{i}. Backup Type: {btype.upper()}")
            print(f"   Date/Time: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Files Processed: {count}")
            if src:
                print(f"   Source: {src}")
            if dst:
                print(f"   Destination: {dst}")
            print("-"*60)
        
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"❌ Error retrieving history: {e}")
        logging.error(f"Failed to retrieve backup history: {e}")

def update_file_record(file_path, size, mtime):
    """Update file record in database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        cursor.execute('''
            INSERT OR REPLACE INTO files (file_path, file_size, last_modified, last_backup)
            VALUES (?, ?, ?, ?)
        ''', (file_path, size, mtime, timestamp))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Failed to update file record for {file_path}: {e}")

def remove_file_record(file_path):
    """Remove file record from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM files WHERE file_path = ?', (file_path,))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Failed to remove file record for {file_path}: {e}")

def get_all_file_records():
    """Get all file records as dictionary"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT file_path, file_size, last_modified FROM files')
        rows = cursor.fetchall()
        conn.close()
        
        return {
            row[0]: {'size': row[1], 'mtime': row[2]}
            for row in rows
        }
    except Exception as e:
        logging.error(f"Failed to get file records: {e}")
        return {}

def record_backup(backup_type, timestamp, file_count, source_path, backup_path):
    """Record backup operation in database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO backups (backup_type, timestamp, file_count, source_path, backup_path)
            VALUES (?, ?, ?, ?, ?)
        ''', (backup_type, timestamp, file_count, source_path, backup_path))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Failed to record backup: {e}")

def get_paths():
    """Get source and backup paths from user"""
    print("\nEnter backup paths:")
    source = input("Source directory: ").strip()
    backup = input("Backup directory: ").strip()
    
    if not source or not backup:
        print("❌ Both paths are required!")
        return None, None
    
    return source, backup

def show_menu():
    """Display main menu"""
    print("\n" + "="*60)
    print("        🗄️  BACKUP MANAGER")
    print("="*60)
    print("1. Full Backup    - Copy all files")
    print("2. Smart Backup   - Copy only new/changed files")
    print("3. Clean Backup   - Remove orphaned files from backup")
    print("4. View History   - Show all backup operations")
    print("5. Exit")
    print("="*60)

def main():
    """Main entry point"""
    setup_logging()
    
    logging.info("="*60)
    logging.info("Backup Manager App Started")
    logging.info("="*60)
    
    if not init_database():
        print("❌ Failed to initialize database. Check log file.")
        return 1
    
    while True:
        show_menu()
        choice = input("Select option (1-5): ").strip()
        
        if choice == '1':
            source, backup = get_paths()
            if source and backup:
                full_backup(source, backup)
        
        elif choice == '2':
            source, backup = get_paths()
            if source and backup:
                smart_backup(source, backup)
        
        elif choice == '3':
            source, backup = get_paths()
            if source and backup:
                clean_backup(source, backup)
        
        elif choice == '4':
            view_history()
        
        elif choice == '5':
            print("\n👋 Goodbye!\n")
            logging.info("Backup Manager App Exited")
            break
        
        else:
            print("❌ Invalid choice. Please select 1-5.")
    
    return 0

if __name__ == "__main__":
    exit(main())
