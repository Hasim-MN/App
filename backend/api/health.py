import logging
import yt_dlp
from fastapi import APIRouter
from backend.services.ffmpeg_service import (
    ensure_ffmpeg_initialized, get_ffmpeg_version, get_ffprobe_version
)
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
            }
        },
        "limits": {
            "max_file_size_gb": settings.MAX_FILE_SIZE_BYTES / (1024**3),
            "max_concurrent_jobs": settings.MAX_CONCURRENT_JOBS,
            "job_retention_minutes": settings.JOB_RETENTION_SECONDS // 60
        }
    }
