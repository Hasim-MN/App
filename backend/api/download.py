import asyncio
import logging
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from backend.models.requests import VideoDownloadRequest, AudioDownloadRequest
from backend.utils.security import validate_url_security
from backend.services.job_manager import job_manager

logger = logging.getLogger("mediaflow.api.download")
router = APIRouter(prefix="/api/download", tags=["Download"])

@router.post("/video")
async def start_video_download(req: VideoDownloadRequest, background_tasks: BackgroundTasks):
    """
    Initiates a video processing & download job.
    """
    url = req.url.strip()
    is_valid, error_msg = validate_url_security(url)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    job_id = await job_manager.create_job(
        media_title=req.title,
        thumbnail=req.thumbnail,
        selected_format=f"Video ({req.container.upper()})"
    )
    
    background_tasks.add_task(job_manager.run_video_job, job_id, req)
    
    return {
        "job_id": job_id,
        "status": "QUEUED",
        "stream_url": f"/api/jobs/{job_id}/stream",
        "status_url": f"/api/jobs/{job_id}"
    }

@router.post("/audio")
async def start_audio_conversion(req: AudioDownloadRequest, background_tasks: BackgroundTasks):
    """
    Initiates an audio extraction & conversion job.
    """
    url = req.url.strip()
    is_valid, error_msg = validate_url_security(url)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    fmt_label = req.format.upper()
    qual_label = req.quality_bitrate or ""
    if req.format.lower() == "flac":
        qual_label = "Lossless"
    elif req.format.lower() == "ogg":
        qual_label = f"Q{req.ogg_quality}"
    elif req.format.lower() == "wav":
        qual_label = f"{req.bit_depth}-bit PCM"
        
    job_id = await job_manager.create_job(
        media_title=req.title,
        thumbnail=req.thumbnail,
        selected_format=f"Audio ({fmt_label} {qual_label})".strip()
    )
    
    background_tasks.add_task(job_manager.run_audio_job, job_id, req)
    
    return {
        "job_id": job_id,
        "status": "QUEUED",
        "stream_url": f"/api/jobs/{job_id}/stream",
        "status_url": f"/api/jobs/{job_id}"
    }
