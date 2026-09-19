#!/data/data/com.termux/files/usr/bin/bash
# ========================================================
# MediaFlow - Android Termux Full Server Setup Script
# Shifts the entire backend onto your phone 100% locally!
# ========================================================

echo "========================================================"
echo "  🎬 Setting up MediaFlow Backend on your Android Phone"
echo "  100% Local - No Laptop, No Cloud, No Limits!"
echo "========================================================"
echo ""

# 1. Update Termux package lists
echo "[1/4] Updating package repositories..."
pkg update -y

# 2. Install essential packages (Python, FFmpeg, Git, Aria2)
echo "[2/4] Installing Python, FFmpeg, Git, and Aria2c..."
pkg install -y python ffmpeg git aria2 clang make libjpeg-turbo

# 3. Upgrade pip and install Python dependencies
echo "[3/4] Installing Python requirements..."
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r backend/requirements.txt

# 4. Create launcher shortcut in home directory
LAUNCHER="$HOME/start_mediaflow.sh"
cat << 'EOF' > "$LAUNCHER"
#!/data/data/com.termux/files/usr/bin/bash
clear
echo "========================================================"
echo "  🚀 Starting MediaFlow Backend on your Android Phone..."
echo "  Server: http://127.0.0.1:8000"
echo "========================================================"
echo ""
cd "$HOME/mediaflow" || cd "$HOME/App"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
EOF

chmod +x "$LAUNCHER"

# Create stop shortcut in home directory
STOPPER="$HOME/stop_mediaflow.sh"
cat << 'EOF' > "$STOPPER"
#!/data/data/com.termux/files/usr/bin/bash
pkill -f "uvicorn backend.main:app" 2>/dev/null
pkill -f "python -m uvicorn" 2>/dev/null
echo "🛑 MediaFlow Server STOPPED."
EOF
chmod +x "$STOPPER"

# Also link to ~/.shortcuts if Termux:Widget is used
mkdir -p "$HOME/.shortcuts"
cp "$LAUNCHER" "$HOME/.shortcuts/MediaFlow-Start" 2>/dev/null || true
cp "$STOPPER" "$HOME/.shortcuts/MediaFlow-Stop" 2>/dev/null || true

echo ""
echo "========================================================"
echo "  🎉 SUCCESS! MediaFlow is installed on your phone!"
echo "========================================================"
echo ""
echo "  To start the server right now, run:"
echo "    bash ~/start_mediaflow.sh"
echo ""
echo "  Then open your MediaFlow Android app, tap Server, and"
echo "  select: http://127.0.0.1:8000"
echo "========================================================"
