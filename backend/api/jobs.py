import os
import json
import logging
from typing import List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse
from backend.models.jobs import JobProgress, JobHistoryItem, JobStatus
from backend.services.job_manager import job_manager

logger = logging.getLogger("mediaflow.api.jobs")
router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

@router.get("/history", response_model=List[JobHistoryItem])
async def get_jobs_history():
    """Returns the recent history of completed jobs."""
    return await job_manager.get_history()

@router.get("/{job_id}", response_model=JobProgress)
async def get_job_status(job_id: str):
    """Returns current status and progress of a specific job."""
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found."
        )
    return job

@router.get("/{job_id}/stream")
async def stream_job_progress(job_id: str):
    """
    Streams real-time job progress updates via Server-Sent Events (SSE).
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found."
        )

    async def event_publisher():
        async for state in job_manager.subscribe(job_id):
            yield {
                "event": "progress",
                "data": json.dumps(state)
            }

    return EventSourceResponse(event_publisher())

@router.get("/{job_id}/download")
async def download_job_file(job_id: str):
    """
    Serves the processed media file as a direct download attachment.
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found."
        )
        
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed yet (current status: {job.status})."
        )
        
    if not job.output_path or not os.path.exists(job.output_path):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Processed file is no longer available on the server."
        )

    filename = job.file_name or os.path.basename(job.output_path)
    
    return FileResponse(
        path=job.output_path,
        filename=filename,
        media_type="application/octet-stream"
    )
