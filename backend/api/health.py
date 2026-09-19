import logging
import yt_dlp
from fastapi import APIRouter
from backend.services.ffmpeg_service import (
    ensure_ffmpeg_initialized, get_ffmpeg_version, get_ffprobe_version
)
from backend.services.torrent_service import get_aria2c_binary, get_aria2c_version
from backend.config import settings

logger = logging.getLogger("mediaflow.api.health")
router = APIRouter(prefix="/api", tags=["Health"])

@router.get("/health")
async def health_check():
    """
    Checks the operational status of server dependencies (FFmpeg, FFprobe, yt-dlp).
    """
    ffmpeg_ok = ensure_ffmpeg_initialized()
    ffmpeg_ver = get_ffmpeg_version()
    ffprobe_ver = get_ffprobe_version()
    
    ytdlp_ver = yt_dlp.version.__version__
    
    overall_status = "ok" if (ffmpeg_ok and ffmpeg_ver and ffprobe_ver) else "degraded"
    
    import os
    import shutil
    
    raw_cookies = (
        os.environ.get("YOUTUBE_COOKIES") or 
        os.environ.get("YOUTUBE_COOKIE") or 
        os.environ.get("COOKIES") or 
        os.environ.get("COOKIE") or 
        os.environ.get("COOKIES_DATA") or
        os.environ.get("COOKIES_TEXT")
    )
    has_cookies = bool(raw_cookies and raw_cookies.strip()) or os.path.exists("cookies.txt")
    cookies_bytes = len(raw_cookies.strip()) if (raw_cookies and raw_cookies.strip()) else 0

    proxy = (
        os.environ.get("HTTP_PROXY") or 
        os.environ.get("HTTPS_PROXY") or 
        os.environ.get("PROXY") or 
        os.environ.get("YOUTUBE_PROXY")
    )

    return {
        "status": overall_status,
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "dependencies": {
            "ffmpeg": {
                "available": bool(ffmpeg_ver),
                "version": ffmpeg_ver
            },
            "ffprobe": {
                "available": bool(ffprobe_ver),
                "version": ffprobe_ver
            },
            "yt_dlp": {
                "available": True,
                "version": ytdlp_ver
            },
            "js_runtime": {
                "node_available": bool(shutil.which("node")),
                "deno_available": bool(shutil.which("deno"))
            },
            "youtube_auth": {
                "cookies_loaded": has_cookies,
                "cookies_bytes": cookies_bytes,
                "proxy_configured": bool(proxy and proxy.strip())
            },
            "torrent": {
                "available": bool(get_aria2c_binary()),
                "engine": "aria2",
                "version": get_aria2c_version()
            }
        },
        "limits": {
            "max_file_size_gb": settings.MAX_FILE_SIZE_BYTES / (1024**3),
            "max_concurrent_jobs": settings.MAX_CONCURRENT_JOBS,
            "job_retention_minutes": settings.JOB_RETENTION_SECONDS // 60
        }
    }


@router.get("/network")
async def get_network_info():
    """
    Returns server network connectivity endpoints:
    - Hostname and mDNS URL (e.g. http://ALIM-PC.local:8000)
    - Local LAN IP (e.g. http://10.148.250.47:8000)
    - Active Cloudflare 5G tunnel URL (if running)
    """
    import socket
    import re
    from pathlib import Path

    hostname = socket.gethostname()
    
    # Try to find local IP
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # connect to a public DNS IP (does not actually send packets)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    # Check for active cloudflared tunnel URL in scripts/tunnel.log
    tunnel_url = None
    log_candidates = [
        Path("scripts/tunnel.log"),
        Path("../scripts/tunnel.log"),
        Path(__file__).parent.parent.parent / "scripts" / "tunnel.log"
    ]
    for log_path in log_candidates:
        if log_path.exists():
            try:
                # Read last 100 lines
                content = log_path.read_text(encoding="utf-8", errors="ignore")
                matches = re.findall(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", content)
                if matches:
                    tunnel_url = matches[-1]
                    break
            except Exception:
                pass

    return {
        "hostname": hostname,
        "local_ip": local_ip,
        "mdns_url": f"http://{hostname.lower()}.local:8000",
        "lan_url": f"http://{local_ip}:8000",
        "tunnel_url": tunnel_url,
        "recommended_phone_url": f"http://{hostname.lower()}.local:8000"
    }

