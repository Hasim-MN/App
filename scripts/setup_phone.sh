#!/data/data/com.termux/files/usr/bin/bash
# ========================================================
# MediaFlow - Android Termux Pure-Python Setup Script
# Zero Rust, Zero Pydantic, Zero Compilation!
# ========================================================

echo "========================================================"
echo "  🎬 Setting up MediaFlow Mobile Engine on your Phone"
echo "  100% Pure Python - Installs in 10 Seconds!"
echo "========================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"

# 1. Install standard Termux packages (Python, FFmpeg, Git)
echo "[1/3] Installing Python and FFmpeg..."
pkg update -y || true
pkg install -y python ffmpeg git || true

# 2. Install yt-dlp (pure Python, NO C/Rust compilation!)
echo "[2/3] Installing yt-dlp (Pure Python)..."
python -m pip install --upgrade pip
python -m pip install yt-dlp

# 3. Create launcher shortcuts in home directory
LAUNCHER="$HOME/start_mediaflow.sh"
cat << EOF > "$LAUNCHER"
#!/data/data/com.termux/files/usr/bin/bash
clear
cd "$APP_DIR" || cd "\$HOME/mediaflow" || cd "\$HOME/App"
python backend/phone_server.py 8000
EOF
chmod +x "$LAUNCHER"

STOPPER="$HOME/stop_mediaflow.sh"
cat << 'EOF' > "$STOPPER"
#!/data/data/com.termux/files/usr/bin/bash
pkill -f "python backend/phone_server.py" 2>/dev/null
pkill -f "phone_server.py" 2>/dev/null
echo "🛑 MediaFlow Mobile Server STOPPED."
EOF
chmod +x "$STOPPER"

mkdir -p "$HOME/.shortcuts"
cp "$LAUNCHER" "$HOME/.shortcuts/MediaFlow-Start" 2>/dev/null || true
cp "$STOPPER" "$HOME/.shortcuts/MediaFlow-Stop" 2>/dev/null || true

echo ""
echo "[3/3] Verifying installation..."
if python -c "import yt_dlp; print('yt-dlp verified!')" 2>/dev/null; then
  echo ""
  echo "========================================================"
  echo "  🎉 SUCCESS! MediaFlow Mobile Engine is ready!"
  echo "========================================================"
  echo ""
  echo "  To start the server right now, run:"
  echo "    bash ~/start_mediaflow.sh"
  echo ""
  echo "  Then in your app, use: http://127.0.0.1:8000"
  echo "========================================================"
else
  echo "⚠️ Installation had a problem. Run 'python -m pip install yt-dlp' manually."
fi
