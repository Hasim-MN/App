#!/usr/bin/env python3
"""
MediaFlow - Pure-Python Mobile Backend Engine
Zero dependencies on Pydantic, Rust, Maturin, or C compilers!
Requires ONLY standard library + yt-dlp.
Runs 100% locally on Android Termux or any Python 3.8+ environment.
"""

import os
import sys
import json
import time
import uuid
import shutil
import urllib.parse
import subprocess
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory jobs database
jobs_lock = threading.Lock()
jobs = {}

def get_ffmpeg_status():
    ffmpeg_ok = shutil.which("ffmpeg") is not None
    return ffmpeg_ok

def format_bytes(size):
    if not size:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def format_duration(seconds):
    if not seconds:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

SUPPORTED_AUDIO_FORMATS = [
    {"format": "mp3", "name": "MP3 Audio", "type": "lossy", "description": "Standard universal MP3", "recommended_quality": "320k", "default_extension": "mp3"},
    {"format": "m4a", "name": "M4A / AAC", "type": "lossy", "description": "High quality Apple AAC", "recommended_quality": "256k", "default_extension": "m4a"},
    {"format": "wav", "name": "WAV Lossless", "type": "uncompressed", "description": "Lossless Studio Audio", "recommended_quality": "Original", "default_extension": "wav"},
    {"format": "flac", "name": "FLAC Lossless", "type": "lossless", "description": "Free Lossless Audio Codec", "recommended_quality": "Level 5", "default_extension": "flac"},
    {"format": "opus", "name": "Opus Audio", "type": "lossy", "description": "Ultra high efficiency codec", "recommended_quality": "160k", "default_extension": "opus"}
]

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class MediaFlowHandler(BaseHTTPRequestHandler):

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE, HEAD")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Range, X-Requested-With")
        self.send_header("Access-Control-Expose-Headers", "Content-Disposition, Content-Length, Content-Range, Accept-Ranges")

    def send_json(self, status_code, data):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = urllib.parse.parse_qs(parsed.query)

        # Root
        if path == "" or path == "/":
            self.send_json(200, {
                "app": "MediaFlow Downloader (Pure-Python Mobile Engine)",
                "status": "online",
                "version": "1.0.0-mobile"
            })
            return

        # Health Check
        if path == "/api/health":
            self.send_json(200, {
                "status": "ok",
                "app_name": "MediaFlow Downloader (Pure Python)",
                "app_version": "1.0.0-mobile",
                "dependencies": {
                    "ffmpeg": {"available": get_ffmpeg_status(), "version": "Termux FFmpeg" if get_ffmpeg_status() else "Not Found"},
                    "ffprobe": {"available": shutil.which("ffprobe") is not None},
                    "yt_dlp": {"available": True, "version": "Active"}
                },
                "limits": {
                    "max_file_size_gb": 4,
                    "max_concurrent_jobs": 5
                }
            })
            return

        # Job History
        if path == "/api/jobs/history":
            with jobs_lock:
                history = [
                    {
                        "job_id": j["job_id"],
                        "title": j.get("media_title", "Media Download"),
                        "thumbnail": j.get("media_thumbnail", ""),
                        "format_type": j.get("selected_format", "video"),
                        "selected_quality": j.get("quality_label", "Best"),
                        "file_size_bytes": j.get("file_size_bytes", 0),
                        "completed_at": j.get("updated_at", time.time()),
                        "file_name": j.get("file_name", "download.mp4")
                    }
                    for j in jobs.values() if j.get("status") == "COMPLETED"
                ]
            self.send_json(200, history)
            return

        # Job Status: /api/jobs/{job_id}
        if path.startswith("/api/jobs/") and not path.endswith("/download") and not path.endswith("/stream"):
            job_id = path.split("/")[3]
            with jobs_lock:
                job = jobs.get(job_id)
            if not job:
                self.send_json(404, {"detail": f"Job {job_id} not found"})
                return
            self.send_json(200, job)
            return

        # Job SSE Stream: /api/jobs/{job_id}/stream
        if path.startswith("/api/jobs/") and path.endswith("/stream"):
            job_id = path.split("/")[3]
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            while True:
                with jobs_lock:
                    job = jobs.get(job_id)
                if not job:
                    break
                data_line = f"data: {json.dumps(job)}\n\n"
                try:
                    self.wfile.write(data_line.encode("utf-8"))
                    self.wfile.flush()
                except Exception:
                    break
                if job.get("status") in ["COMPLETED", "FAILED", "CANCELLED"]:
                    break
                time.sleep(0.5)
            return

        # Job Download File: /api/jobs/{job_id}/download
        if path.startswith("/api/jobs/") and path.endswith("/download"):
            job_id = path.split("/")[3]
            with jobs_lock:
                job = jobs.get(job_id)
            if not job or not job.get("output_path") or not os.path.exists(job["output_path"]):
                self.send_json(404, {"detail": "File not ready or expired"})
                return

            file_path = job["output_path"]
            file_size = os.path.getsize(file_path)
            file_name = job.get("file_name") or os.path.basename(file_path)

            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{urllib.parse.quote(file_name)}"')
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()

            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(64 * 1024)
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                    except Exception:
                        break
            return

        self.send_json(404, {"detail": "Not Found"})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len) if content_len > 0 else b"{}"

        try:
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            self.send_json(400, {"detail": "Invalid JSON payload"})
            return

        # 1. /api/analyze
        if path == "/api/analyze":
            url = body.get("url")
            if not url:
                self.send_json(400, {"detail": "Missing media URL"})
                return

            try:
                import yt_dlp
            except ImportError:
                self.send_json(500, {"detail": "yt-dlp is not installed. Run: pip install yt-dlp"})
                return

            try:
                ydl_opts = {
                    "skip_download": True,
                    "quiet": True,
                    "no_warnings": True,
                    "extract_flat": False,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                formats = []
                raw_formats = info.get("formats", [])
                
                # Find best audio format id for muxing
                best_audio_id = None
                for f in reversed(raw_formats):
                    if f.get("acodec") != "none" and f.get("vcodec") == "none":
                        best_audio_id = f.get("format_id")
                        break

                for f in raw_formats:
                    has_video = f.get("vcodec") != "none" and f.get("vcodec") is not None
                    has_audio = f.get("acodec") != "none" and f.get("acodec") is not None
                    if not has_video and not has_audio:
                        continue

                    height = f.get("height")
                    width = f.get("width")
                    quality = f"{height}p" if height else f.get("format_note", "Auto")
                    if height and height >= 2160:
                        quality = "4K 2160p"
                    elif height and height >= 1440:
                        quality = "2K 1440p"
                    elif height and height >= 1080:
                        quality = "1080p FHD"
                    elif height and height >= 720:
                        quality = "720p HD"

                    formats.append({
                        "format_id": str(f.get("format_id")),
                        "extension": f.get("ext", "mp4"),
                        "quality_label": quality,
                        "resolution": f"{width}x{height}" if width and height else quality,
                        "width": width,
                        "height": height,
                        "fps": f.get("fps"),
                        "video_codec": f.get("vcodec"),
                        "audio_codec": f.get("acodec"),
                        "bitrate_kbps": int(f.get("tbr") or f.get("vbr") or 0),
                        "estimated_size_bytes": f.get("filesize") or f.get("filesize_approx"),
                        "has_video": has_video,
                        "has_audio": has_audio,
                        "is_dash_video": has_video and not has_audio,
                        "audio_format_id_for_merge": best_audio_id if (has_video and not has_audio) else None
                    })

                media_info = {
                    "url": url,
                    "title": info.get("title") or "Unknown Media",
                    "thumbnail": info.get("thumbnail") or "",
                    "duration_seconds": info.get("duration", 0),
                    "duration_formatted": format_duration(info.get("duration", 0)),
                    "source": info.get("extractor_key") or "Web",
                    "uploader": info.get("uploader") or info.get("channel") or "",
                    "view_count": info.get("view_count"),
                    "video_formats": formats,
                    "supported_audio_formats": SUPPORTED_AUDIO_FORMATS
                }

                self.send_json(200, media_info)
            except Exception as e:
                self.send_json(500, {"detail": f"Media extraction failed: {str(e)}"})
            return

        # 2. /api/download/video or /api/download/audio
        if path in ["/api/download/video", "/api/download/audio"]:
            url = body.get("url")
            if not url:
                self.send_json(400, {"detail": "Missing media URL"})
                return

            job_id = str(uuid.uuid4())
            is_audio = path == "/api/download/audio"

            with jobs_lock:
                jobs[job_id] = {
                    "job_id": job_id,
                    "status": "QUEUED",
                    "phase": "Queued",
                    "percent": 0.0,
                    "speed_str": "",
                    "eta_str": "",
                    "downloaded_bytes": 0,
                    "total_bytes": 0,
                    "file_name": "",
                    "file_size_bytes": 0,
                    "media_title": body.get("title") or "Downloading...",
                    "media_thumbnail": body.get("thumbnail") or "",
                    "selected_format": body.get("format") or body.get("format_id") or "best",
                    "output_path": "",
                    "error": None,
                    "created_at": time.time(),
                    "updated_at": time.time(),
                    "download_url": f"/api/jobs/{job_id}/download"
                }

            # Start worker thread
            thread = threading.Thread(
                target=self._run_download_job,
                args=(job_id, url, body, is_audio),
                daemon=True
            )
            thread.start()

            self.send_json(200, {
                "job_id": job_id,
                "stream_url": f"/api/jobs/{job_id}/stream",
                "status_url": f"/api/jobs/{job_id}"
            })
            return

        self.send_json(404, {"detail": "Not Found"})

    def _run_download_job(self, job_id, url, body, is_audio):
        try:
            import yt_dlp
        except ImportError:
            with jobs_lock:
                jobs[job_id]["status"] = "FAILED"
                jobs[job_id]["error"] = "yt-dlp is not installed"
            return

        def progress_hook(d):
            if d.get("status") == "downloading":
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                pct = (downloaded / total * 100) if total > 0 else 0.0
                speed = d.get("speed") or 0
                eta = d.get("eta") or 0

                with jobs_lock:
                    if job_id in jobs:
                        jobs[job_id]["status"] = "DOWNLOADING"
                        jobs[job_id]["phase"] = "Downloading stream..."
                        jobs[job_id]["percent"] = round(pct, 1)
                        jobs[job_id]["downloaded_bytes"] = downloaded
                        jobs[job_id]["total_bytes"] = total
                        jobs[job_id]["speed_str"] = f"{format_bytes(speed)}/s" if speed else ""
                        jobs[job_id]["eta_str"] = f"{int(eta)}s" if eta else ""
                        jobs[job_id]["updated_at"] = time.time()

            elif d.get("status") == "finished":
                with jobs_lock:
                    if job_id in jobs:
                        jobs[job_id]["phase"] = "Finalizing file..."
                        jobs[job_id]["percent"] = 99.0
                        jobs[job_id]["updated_at"] = time.time()

        job_dir = DOWNLOADS_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        outtmpl = str(job_dir / "%(title).200s.%(ext)s")

        format_sel = "best"
        postprocessors = []

        if is_audio:
            target_fmt = body.get("format", "mp3")
            format_sel = "bestaudio/best"
            if get_ffmpeg_status():
                postprocessors.append({
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": target_fmt,
                    "preferredquality": body.get("quality_bitrate", "320").replace("k", ""),
                })
        else:
            fmt_id = body.get("format_id")
            audio_id = body.get("audio_format_id")
            if fmt_id and audio_id and fmt_id != audio_id:
                format_sel = f"{fmt_id}+{audio_id}/best"
            elif fmt_id:
                format_sel = f"{fmt_id}+bestaudio/best"
            else:
                format_sel = "bestvideo+bestaudio/best"

        ydl_opts = {
            "format": format_sel,
            "outtmpl": outtmpl,
            "nopart": True,
            "progress_hooks": [progress_hook],
            "quiet": True,
            "no_warnings": True,
        }
        if postprocessors:
            ydl_opts["postprocessors"] = postprocessors

        try:
            with jobs_lock:
                jobs[job_id]["status"] = "DOWNLOADING"
                jobs[job_id]["phase"] = "Connecting to source..."

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info)

            # Check downloaded file
            actual_file = None
            if os.path.exists(downloaded_file):
                actual_file = downloaded_file
            else:
                # Look for converted audio or muxed extension
                base_without_ext = os.path.splitext(downloaded_file)[0]
                candidates = list(job_dir.glob("*"))
                if candidates:
                    actual_file = str(candidates[0])

            if actual_file and os.path.exists(actual_file):
                file_size = os.path.getsize(actual_file)
                file_name = os.path.basename(actual_file)

                with jobs_lock:
                    jobs[job_id]["status"] = "COMPLETED"
                    jobs[job_id]["phase"] = "Completed"
                    jobs[job_id]["percent"] = 100.0
                    jobs[job_id]["output_path"] = actual_file
                    jobs[job_id]["file_name"] = file_name
                    jobs[job_id]["file_size_bytes"] = file_size
                    jobs[job_id]["media_title"] = info.get("title") or file_name
                    jobs[job_id]["media_thumbnail"] = info.get("thumbnail") or ""
                    jobs[job_id]["updated_at"] = time.time()
            else:
                raise Exception("Output file was not produced by downloader")

        except Exception as e:
            with jobs_lock:
                jobs[job_id]["status"] = "FAILED"
                jobs[job_id]["phase"] = "Failed"
                jobs[job_id]["error"] = str(e)
                jobs[job_id]["updated_at"] = time.time()

def run(port=8000, host="0.0.0.0"):
    server = ThreadedHTTPServer((host, port), MediaFlowHandler)
    print("=" * 60)
    print(f"  [+] MediaFlow Pure-Python Mobile Server Active!")
    print(f"  URL: http://127.0.0.1:{port} (all interfaces {host}:{port})")
    print(f"  FFmpeg: {'Ready' if get_ffmpeg_status() else 'Not installed (direct stream mode)'}")
    print("  Zero Rust, Zero Pydantic, Zero Compilation!")
    print("=" * 60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.shutdown()

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run(port=port)
