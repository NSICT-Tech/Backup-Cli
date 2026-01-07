#!/bin/bash
# Quick Installation Script for Backup Manager & Checker

set -e

echo "============================================================"
echo "  🗄️  Backup Manager & Checker - Installation"
echo "============================================================"
echo ""

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed."
    echo "Installing Python3..."
    sudo apt update
    sudo apt install python3 -y
    echo "✅ Python3 installed!"
else
    echo "✅ Python3 is already installed: $(python3 --version)"
fi

echo ""

# Create directories
echo "📁 Creating directories..."
mkdir -p ~/bin
mkdir -p ~/.backup_manager

echo "✅ Directories created!"
echo ""

# Check if scripts exist
CHECKER_PATH="$HOME/bin/backup_checker.py"
MANAGER_PATH="$HOME/bin/backup_manager.py"

if [ ! -f "$CHECKER_PATH" ] || [ ! -f "$MANAGER_PATH" ]; then
    echo "⚠️  Scripts not found in ~/bin/"
    echo ""
    echo "Please follow these steps:"
    echo "1. Save 'backup_checker.py' to: $CHECKER_PATH"
    echo "2. Save 'backup_manager.py' to: $MANAGER_PATH"
    echo "3. Run this installer again"
    echo ""
    exit 1
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x "$CHECKER_PATH"
chmod +x "$MANAGER_PATH"
echo "✅ Scripts are now executable!"
echo ""

# Test the scripts
echo "🧪 Testing backup checker..."
if python3 "$CHECKER_PATH" > /dev/null 2>&1; then
    echo "✅ Backup checker works!"
else
    echo "⚠️  Backup checker test failed (this is OK if it's the first run)"
fi
echo ""

# Offer to set up cron
echo "============================================================"
echo "  ⏰ Automatic Backup Checking Setup"
echo "============================================================"
echo ""
echo "Would you like to set up automatic backup checking?"
echo "This will check your backup status every 12 hours (8 AM and 8 PM)"
echo ""
read -p "Set up automatic checking? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Create cron job
    CRON_CMD="0 8,20 * * * /usr/bin/python3 $CHECKER_PATH >> $HOME/.backup_manager/cron.log 2>&1"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "backup_checker.py"; then
        echo "⚠️  Cron job already exists!"
    else
        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
        echo "✅ Automatic checking enabled!"
        echo "   Checks will run at 8 AM and 8 PM daily"
    fi
else
    echo "⏭️  Skipped automatic checking setup"
    echo "   You can set it up later by running: crontab -e"
fi

echo ""
echo "============================================================"
echo "  🎉 Installation Complete!"
echo "============================================================"
echo ""
echo "📝 What's Next?"
echo ""
echo "1. Run your first backup:"
echo "   $ python3 ~/bin/backup_manager.py"
echo ""
echo "2. Check backup status anytime:"
echo "   $ python3 ~/bin/backup_checker.py"
echo ""
echo "3. View logs:"
echo "   $ tail -f ~/.backup_manager/checker.log"
echo "   $ tail -f ~/.backup_manager/manager.log"
echo ""
echo "📚 For full documentation, see README.md"
echo ""
echo "============================================================"
echo "Happy backing up! 🗄️"
echo "============================================================"
