#!/data/data/com.termux/files/usr/bin/bash
# ========================================================
# MediaFlow - Android Phone Server Runner
# Starts the pure-Python mobile backend on port 8000
# ========================================================

clear
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"

cd "$APP_DIR" || exit 1

python backend/phone_server.py 8000
