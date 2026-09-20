#!/data/data/com.termux/files/usr/bin/bash
# ========================================================
# MediaFlow - Android Phone Server Runner
# Starts the backend locally on your mobile device (port 8000)
# ========================================================

clear
echo "========================================================"
echo "  🚀 MediaFlow Downloader - Local Phone Backend"
echo "  Status: Starting on 127.0.0.1:8000 (No Laptop Needed!)"
echo "========================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"

cd "$APP_DIR" || exit 1

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
