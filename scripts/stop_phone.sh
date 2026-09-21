#!/data/data/com.termux/files/usr/bin/bash
# ========================================================
# MediaFlow - Stop Phone Backend
# ========================================================

pkill -f "python backend/phone_server.py" 2>/dev/null
pkill -f "phone_server.py" 2>/dev/null

echo "========================================================"
echo "  🛑 MediaFlow Server has been STOPPED on your phone."
echo "========================================================"
