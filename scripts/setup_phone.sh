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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"

# 1. Update Termux package lists
echo "[1/4] Updating package repositories..."
pkg update -y || true

# 2. Install essential packages (Python, FFmpeg, Git, Aria2)
echo "[2/4] Installing Python, FFmpeg, Git, and Aria2c..."
pkg install -y python ffmpeg git aria2 clang make libjpeg-turbo || true

# 3. Upgrade pip and install pre-built pydantic-core for Android ARM64
echo "[3/5] Installing Python tools & pre-built pydantic-core..."
python -m pip install --upgrade pip setuptools wheel
echo "Fetching pre-built pydantic-core wheel for Android..."
curl -sL https://raw.githubusercontent.com/Eutalix/android-pydantic-core/main/install_pydantic_core.sh | bash || {
  echo "Fallback: trying extra-index-url..."
  python -m pip install pydantic-core --extra-index-url https://eutalix.github.io/android-pydantic-core/
}

# 4. Install remaining Python dependencies
echo "[4/5] Installing Python requirements..."
python -m pip install -r "$APP_DIR/backend/requirements-phone.txt"

# 4. Create launcher shortcut in home directory
LAUNCHER="$HOME/start_mediaflow.sh"
cat << EOF > "$LAUNCHER"
#!/data/data/com.termux/files/usr/bin/bash
clear
echo "========================================================"
echo "  🚀 Starting MediaFlow Backend on your Android Phone..."
echo "  Server: http://127.0.0.1:8000 (also http://0.0.0.0:8000)"
echo "========================================================"
echo ""
cd "$APP_DIR" || cd "\$HOME/mediaflow" || cd "\$HOME/App"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
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
echo "[5/5] Verifying installation..."
if python -c "import fastapi, uvicorn, yt_dlp, pydantic; print('All core modules verified successfully!')" 2>/dev/null; then
  echo ""
  echo "========================================================"
  echo "  🎉 SUCCESS! MediaFlow is ready on your phone!"
  echo "========================================================"
  echo ""
  echo "  To start the server right now, run:"
  echo "    bash ~/start_mediaflow.sh"
  echo ""
  echo "  Then in your app, use: http://127.0.0.1:8000"
  echo "========================================================"
else
  echo ""
  echo "========================================================"
  echo "  ⚠️ Warning: Core dependencies could not be imported."
  echo "  Please check the error output above."
  echo "========================================================"
fi
