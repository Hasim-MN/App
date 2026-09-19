# 🎬 MediaFlow Downloader

**MediaFlow Downloader** is a full-stack media inspection, stream merging, and audio conversion platform. It enables users to inspect media stream formats from authorized public URLs, download high-definition video formats with intelligent FFmpeg stream-copying, and convert audio into 9 studio-grade audio codecs.

---

## ✨ Features

### 🎥 High-Definition Video Inspection & Merging
- **Dynamic Quality Matrix**: Discovers actual available video streams (144p, 240p, 360p, 480p, 720p HD, 1080p Full HD, 1440p 2K, 2160p 4K, 4320p 8K).
- **Separate Stream Merging**: Automatically pairs high-res DASH video streams with the best audio track using FFmpeg stream copying (`-c copy`) with zero quality loss and minimal CPU usage.
- **Container Switching**: Supports `MP4`, `WebM`, and `MKV` output formats.
- **Codec Transparency**: Reports video codecs (H.264, H.265/HEVC, VP9, AV1) and audio streams.

### 🎵 9-Format Audio Conversion Suite
- **Dynamic Codec-Aware Controls**:
  - **MP3**: Bitrates (64k to 320k) with recommended 320 kbps high-fidelity setting.
  - **FLAC**: Lossless master audio with selectable Bit Depth (16-bit, 24-bit), Sample Rate (44.1 kHz to 192 kHz), and Compression Levels (0–8).
  - **WAV**: Uncompressed studio PCM with 16-bit, 24-bit, and 32-bit Float options.
  - **AAC & M4A**: Advanced Audio Coding with Apple Music standard bitrates and faststart containers.
  - **OPUS**: Next-gen speech and music codec with ultra-low bitrates up to 256 kbps.
  - **OGG Vorbis**: Variable bitrate quality levels Q0 to Q10 with descriptive presets.
  - **ALAC & AIFF**: Apple Lossless and studio AIFF PCM.
- **Direct Stream Extraction (Zero Loss)**: One-click "Download Original Audio" extracts the native stream directly without transcoding.
- **Source Audio Inspection**: Shows input codec, bitrate, sample rate, and channels.
- **Audio Upsampling Caution**: Informs users when converting lower-bitrate sources to higher settings to prevent misconceptions about restored quality.
- **Advanced Engineering Options**: Audio channel routing (Mono, Stereo) and optional EBU R128 loudness normalization.

### ⚡ Real-Time Progress & Modern UX
- **Server-Sent Events (SSE)**: Live streaming progress updates with percentage, download speed (MB/s), and ETA calculations.
- **Dark Charcoal SaaS Interface**: Sleek obsidian backdrop with neon cyan/indigo accents and responsive cards for mobile.
- **Local History Drawer**: Session history with instant re-download options.

### 🛡️ Enterprise Security & SSRF Protection
- **Strict SSRF Defense**: Validates domain IPs against loopback (`127.0.0.0/8`), private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`), IPv6 link-local/unique-local, and cloud metadata endpoints (`169.254.169.254`).
- **Safe Subprocess Execution**: Arguments strictly passed as sanitised arrays (`shell=False`).
- **Isolated Sandboxes**: Unique UUID-based job directories with automated 30-minute retention garbage collection.
- **Ethical Downloading**: Does NOT circumvent DRM, paywalls, or private authentication restrictions.

---

## 🛠️ Architecture

```
d:/APP/
├── backend/
│   ├── main.py                     # FastAPI entry point with CORS & Lifespan
│   ├── config.py                   # App settings, limits, retention policies
│   ├── requirements.txt            # Python dependencies
│   ├── api/                        # REST & SSE API endpoints
│   │   ├── analyze.py              # POST /api/analyze
│   │   ├── download.py             # POST /api/download/video & /api/download/audio
│   │   ├── jobs.py                 # GET /api/jobs/{id}, /stream (SSE), /download
│   │   └── health.py               # GET /api/health
│   ├── services/
│   │   ├── extractor.py            # yt-dlp wrapper with DRM detection
│   │   ├── media_analyzer.py       # Stream inspection & format grouping
│   │   ├── ffmpeg_service.py       # Safe FFmpeg execution with progress hooks
│   │   ├── audio_converter.py      # 9-format audio conversion engine
│   │   ├── video_merger.py         # Video+Audio stream-copy & remuxing
│   │   └── job_manager.py          # In-memory async job queue & SSE broker
│   ├── models/                     # Pydantic schemas (media, jobs, requests)
│   └── utils/                      # Security validation, filename sanitization, temp files
├── frontend/                       # Next.js 16 App Router UI
│   ├── src/app/                    # App layouts, pages, globals.css
│   ├── src/components/             # UI Components (Navbar, Cards, Tables, AudioPanel)
│   └── src/lib/                    # API client, types, formatters
├── Dockerfile                      # Production container build
└── docker-compose.yml              # Multi-service composition
```

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- Python 3.10+ (with pip)
- Node.js 18+ (with npm)
- FFmpeg (automatically provided via `static-ffmpeg` if not installed globally)

### 2. Start Backend
```bash
# Navigate to workspace root
cd d:/APP

# Install backend dependencies
py -m pip install -r backend/requirements.txt

# Run FastAPI server
py -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Backend API will be accessible at: `http://localhost:8000` (Interactive Swagger Docs at `http://localhost:8000/docs`)

### 3. Start Frontend
```bash
# Navigate to frontend folder
cd d:/APP/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
Frontend web interface will be accessible at: `http://localhost:3000`

---

## 📱 Android Mobile App (.APK)

MediaFlow Downloader can be installed and run natively on any Android smartphone or tablet.

### 📥 Downloading the APK from GitHub
1. Go to your repository's **Releases** tab on GitHub (or the **Actions** tab for latest artifact builds).
2. Download `MediaFlow-Downloader.apk`.
3. Open the `.apk` file on your Android device and tap **Install** (allow *Install from Unknown Sources* if prompted).

### ⚙️ Connecting the App to your Backend
Because the app runs on your phone:
1. Tap the **Server** icon in the top header.
2. Enter your backend API URL:
   - **Local Wi-Fi**: `http://<your-computer-ip>:8000` (e.g. `http://192.168.1.10:8000`)
   - **Cloud/Hosted**: `https://your-api-domain.com`
3. Tap **Test Connection** & **Save & Connect**.

### 📲 Shift Server 100% Onto Your Phone (Zero Laptop Needed!)

If you want MediaFlow to work **completely independently** even when your laptop is completely shut down or turned off:

You can run the MediaFlow Python backend directly inside your Android phone using **Termux** (free Linux terminal for Android):

#### Step 1: Install Termux on your phone
- Download and install **Termux** from [F-Droid](https://f-droid.org/packages/com.termux/) or GitHub ([Termux Releases](https://github.com/termux/termux-app/releases)).

#### Step 2: Run the 1-Line Setup Command
Open Termux on your phone, paste this single command, and press **Enter**:
```bash
pkg update -y && pkg install -y git python ffmpeg aria2 && git clone https://github.com/Hasim-MN/App.git mediaflow && cd mediaflow && bash scripts/setup_phone.sh
```
This automatically configures Python, FFmpeg, and downloads all dependencies right inside your phone!

#### Step 3: Launch and Connect
1. In Termux, whenever you want to start the server, type:
   ```bash
   bash ~/start_mediaflow.sh
   ```
2. Open your **MediaFlow Downloader** app on your phone.
3. Tap the **Server** icon in the header and select:
   ```
   http://127.0.0.1:8000
   ```
4. Tap **Save & Connect**.

MediaFlow now runs **100% locally on your phone**! You can power off, shut down, or leave your laptop anywhere — all downloads, video stream copying, audio conversions, and torrents happen directly on your phone!

---

### 💻 Alternative: 24/7 Always-On Mode (Using Laptop with Lid Closed)
If you prefer your laptop to do the heavy downloading while plugged in with the lid closed:
1. Double-click `scripts/setup_lid_always_on.bat` (configures Windows not to sleep when closed).
2. Double-click `scripts/install_auto_start_service.bat` (auto-starts backend on PC boot).
3. Connect your phone via `http://alim-pc.local:8000` (on home Wi-Fi) or 5G Cloudflare Tunnel.



---

## 🐳 Docker Deployment

To build and run MediaFlow Downloader using Docker:

```bash
docker-compose up -d --build
```
Access the application at `http://localhost:3000`.

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/analyze` | Analyzes URL, parses video qualities and audio specs |
| `POST` | `/api/download/video` | Enqueues a video stream merge/download job |
| `POST` | `/api/download/audio` | Enqueues an audio extraction & conversion job |
| `GET` | `/api/jobs/{job_id}` | Polls job status and progress percentage |
| `GET` | `/api/jobs/{job_id}/stream` | Streams live progress via Server-Sent Events (SSE) |
| `GET` | `/api/jobs/{job_id}/download` | Serves the generated media file for download |
| `GET` | `/api/jobs/history` | Retrieves recent completed jobs history |
| `GET` | `/api/health` | Diagnostic status of FFmpeg, FFprobe, and yt-dlp |

---

## ⚖️ Legal & Ethical Usage Notice
MediaFlow Downloader is intended strictly for media that the user owns, content in the public domain, or openly licensed media where downloading is authorized. It does not bypass copyright protection, DRM encryption, paywalls, or access controls.
#   M y   N e w   P r o j e c t  
 #   M y   n e w   p r o j e c t  
 