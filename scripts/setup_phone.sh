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

# 3. Install pre-built pydantic-core for Android ARM64
echo "[3/5] Installing pre-compiled pydantic-core for Android..."
python -m pip install --upgrade pip setuptools wheel

PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
PY_TAG="cp${PY_MAJOR}${PY_MINOR}"
SITE_DIR=$(python3 -c "import site; print(site.getsitepackages()[0])")

TMP_WHL="$HOME/pydantic_core.whl"
echo "Downloading pre-compiled pydantic-core for Python ${PY_MAJOR}.${PY_MINOR} (${PY_TAG})..."
curl -sL -o "$TMP_WHL" "https://github.com/Eutalix/android-pydantic-core/releases/download/v2.46.3/pydantic_core-2.46.3-${PY_TAG}-${PY_TAG}-linux_aarch64.whl"

if [ -f "$TMP_WHL" ] && [ -s "$TMP_WHL" ]; then
  echo "Unpacking pydantic-core directly into $SITE_DIR..."
  python3 -m zipfile -e "$TMP_WHL" "$SITE_DIR"
  rm -f "$TMP_WHL"
fi

if python3 -c "import pydantic_core; print('pydantic_core ready!')" 2>/dev/null; then
  echo "✓ pydantic_core successfully loaded!"
else
  echo "Attempting fallback installation..."
  python3 -m pip install pydantic-core --extra-index-url https://eutalix.github.io/android-pydantic-core/ || true
fi

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
