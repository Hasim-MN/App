#!/data/data/com.termux/files/usr/bin/bash
# ========================================================
# MediaFlow - Stop Phone Backend
# ========================================================

pkill -f "uvicorn backend.main:app" 2>/dev/null
pkill -f "python -m uvicorn" 2>/dev/null

echo "========================================================"
echo "  🛑 MediaFlow Server has been STOPPED on your phone."
echo "========================================================"
