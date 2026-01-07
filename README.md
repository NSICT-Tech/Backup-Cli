# 🗄️ Backup Manager & Checker - Complete Guide

Two robust CLI applications for Ubuntu/Debian that work together to manage your file backups with automated alerts.

---

## 📦 What's Included

### 1️⃣ **Backup Checker App** (`backup_checker.py`)
- ✅ Monitors when your last backup was performed
- ✅ Alerts you if backup is overdue (>3 days)
- ✅ Can run automatically every 12 hours via cron
- ✅ Logs all checks and alerts
- ✅ Never crashes - handles all errors gracefully

### 2️⃣ **Backup Manager App** (`backup_manager.py`)
- ✅ **Full Backup**: Copies all files from source to backup
- ✅ **Smart Backup**: Only copies new or changed files (by size)
- ✅ **Clean Backup**: Removes orphaned files from backup location
- ✅ **History View**: Shows complete backup history with dates and file counts
- ✅ Interactive CLI menu system
- ✅ Complete error handling and logging

---

## 🔧 Installation

### Step 1: Save the Scripts

Save both Python scripts to your system:

```bash
# Create a directory for the scripts
mkdir -p ~/bin
cd ~/bin

# Save backup_checker.py and backup_manager.py to this directory
# (Use the code artifacts provided above)

# Make them executable
chmod +x backup_checker.py backup_manager.py
```

### Step 2: Install Python3 (if not already installed)

```bash
sudo apt update
sudo apt install python3 -y
```

### Step 3: Test the Installation

```bash
# Test the checker
python3 ~/bin/backup_checker.py

# Test the manager
python3 ~/bin/backup_manager.py
```

---

## 🚀 Usage

### Running Backup Manager (Interactive)

```bash
python3 ~/bin/backup_manager.py
```

You'll see a menu:

```
============================================================
        🗄️  BACKUP MANAGER
============================================================
1. Full Backup    - Copy all files
2. Smart Backup   - Copy only new/changed files
3. Clean Backup   - Remove orphaned files from backup
4. View History   - Show all backup operations
5. Exit
============================================================
```

**Example Workflow:**

1. **First time?** Choose option `1` (Full Backup)
   - Enter source: `/home/yourname/Documents`
   - Enter backup: `/media/backup_drive/Documents`

2. **Daily backups?** Choose option `2` (Smart Backup)
   - Only copies new or changed files (much faster!)

3. **Deleted files from source?** Choose option `3` (Clean Backup)
   - Removes files from backup that no longer exist in source

4. **Check history?** Choose option `4` (View History)
   - See all your past backups with timestamps and file counts

### Running Backup Checker (Manual)

```bash
python3 ~/bin/backup_checker.py
```

Output examples:

**When backup is up to date:**
```
✅ Backup status: OK
Last backup: 2026-01-05 14:30:00
Next backup recommended: 2026-01-08
```

**When backup is overdue:**
```
============================================================
⚠️  BACKUP ALERT!
============================================================
Last backup: 2026-01-01 10:00:00
Days since backup: 5
Your data is important. Please back it up today!
Run: python3 backup_manager.py
============================================================
```

---

## 🤖 Automated Checking with Cron

To automatically check every 12 hours:

### Step 1: Open crontab

```bash
crontab -e
```

### Step 2: Add these lines

```bash
# Check backup status every 12 hours (8 AM and 8 PM)
0 8,20 * * * /usr/bin/python3 /home/YOURNAME/bin/backup_checker.py >> /home/YOURNAME/.backup_manager/cron.log 2>&1
```

Replace `YOURNAME` with your actual username!

### Step 3: Save and exit

The checker will now run automatically twice per day.

---

## 📊 How the Apps Work Together

```
┌─────────────────────────────────────────────────────────┐
│                    BACKUP SYSTEM                        │
└─────────────────────────────────────────────────────────┘

1️⃣ BACKUP CHECKER (backup_checker.py)
   ↓
   Reads: ~/.backup_manager/backups.db
   ↓
   Checks: When was last backup?
   ↓
   [More than 3 days ago?]
   ↓
   YES → Shows alert: "⚠️ BACKUP ALERT!"
   NO  → Shows: "✅ Backup status: OK"

2️⃣ BACKUP MANAGER (backup_manager.py)
   ↓
   You run a backup (Full/Smart/Clean)
   ↓
   Updates: ~/.backup_manager/backups.db
   ↓
   Records:
   - Last backup date
   - Files copied/modified
   - Backup type
   - Source/destination paths
   ↓
   Checker now knows backup is current!
```

---

## 🗄️ Database Structure

Location: `~/.backup_manager/backups.db`

### Tables:

**`meta` table:**
```
key                    | value
-----------------------|------------------
last_backup_date       | 2026-01-06T10:30:00
```

**`backups` table:**
```
id | backup_type | timestamp           | file_count | source_path | backup_path
---|-------------|---------------------|------------|-------------|-------------
1  | full        | 2026-01-01T08:00:00 | 1543       | /home/docs  | /media/backup
2  | smart       | 2026-01-05T14:30:00 | 23         | /home/docs  | /media/backup
```

**`files` table:**
```
id | file_path           | file_size | last_modified  | last_backup
---|---------------------|-----------|----------------|-------------------
1  | documents/file.txt  | 4096      | 1704456000.0   | 2026-01-05T14:30:00
2  | images/photo.jpg    | 2048000   | 1704456100.0   | 2026-01-05T14:30:00
```

---

## 📝 Log Files

All operations are logged:

- **Checker logs**: `~/.backup_manager/checker.log`
- **Manager logs**: `~/.backup_manager/manager.log`

View logs:
```bash
tail -f ~/.backup_manager/checker.log
tail -f ~/.backup_manager/manager.log
```

---

## 🔥 Common Use Cases

### Daily Backup Routine
```bash
# Run this every day (manually or via cron)
python3 ~/bin/backup_manager.py
# Choose: 2 (Smart Backup)
# Enter your paths
```

### Weekly Full Backup
```bash
# Run this once a week
python3 ~/bin/backup_manager.py
# Choose: 1 (Full Backup)
```

### After Deleting Files
```bash
# Sync deletions to backup
python3 ~/bin/backup_manager.py
# Choose: 3 (Clean Backup)
```

### Check Backup Status Anytime
```bash
python3 ~/bin/backup_checker.py
```

---

## 🛡️ Error Handling Features

Both apps are designed to **NEVER crash**:

✅ **Database connection issues** → Logged, user notified, app continues  
✅ **Missing directories** → Clear error message shown  
✅ **Permission errors** → Logged and skipped  
✅ **Disk full** → Error logged, operation stops gracefully  
✅ **Corrupted files** → Skipped and logged  
✅ **Network drive disconnected** → Error shown, doesn't crash  

All errors are written to log files for review.

---

## 📋 Backup Type Comparison

| Feature | Full Backup | Smart Backup | Clean Backup |
|---------|-------------|--------------|--------------|
| Copies all files | ✅ Yes | ❌ No | ❌ No |
| Copies only new/changed | ❌ No | ✅ Yes | ❌ No |
| Removes deleted files | ❌ No | ❌ No | ✅ Yes |
| Speed | 🐢 Slow | ⚡ Fast | ⚡ Fast |
| First backup | ✅ Required | ❌ Not recommended | ❌ Not applicable |
| Daily use | ⚠️ Overkill | ✅ Perfect | ⚠️ As needed |

**Recommended workflow:**
1. First time: **Full Backup**
2. Daily: **Smart Backup**
3. After cleaning up files: **Clean Backup**
4. Monthly: **Full Backup** (to ensure everything is synchronized)

---

## 🔍 Troubleshooting

### "No backup history found"
- You haven't run a backup yet!
- Solution: Run `backup_manager.py` and do a Full Backup

### "Source directory does not exist"
- Check your path for typos
- Make sure you're using absolute paths like `/home/user/Documents`

### "Permission denied"
- Check that you have read access to source
- Check that you have write access to backup location

### Logs not appearing
- Check `~/.backup_manager/` directory exists
- Run: `ls -la ~/.backup_manager/`

---

## 📬 Support

For issues or questions:
1. Check log files in `~/.backup_manager/`
2. Verify Python3 is installed: `python3 --version`
3. Check file permissions: `ls -l ~/bin/backup_*.py`

---

## 🎯 Quick Start Checklist

- [ ] Install Python3
- [ ] Save both scripts to `~/bin/`
- [ ] Make scripts executable (`chmod +x`)
- [ ] Run first Full Backup
- [ ] Set up cron job for automated checking
- [ ] Run Smart Backup daily
- [ ] Check History weekly

---

**Made with ❤️ for reliable backups!**
