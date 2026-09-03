import os
import shutil
import time
import logging
from pathlib import Path
from typing import Optional
from backend.config import settings

logger = logging.getLogger("mediaflow.files")

def get_job_temp_dir(job_id: str) -> Path:
    """Creates and returns an isolated temporary directory for a specific job."""
    # Ensure job_id contains only alphanumeric/hyphens
    safe_job_id = "".join(c for c in job_id if c.isalnum() or c in "-_")
    if not safe_job_id:
        safe_job_id = "default_job"
    
    job_dir = Path(settings.BASE_TEMP_DIR) / safe_job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir

def cleanup_job_dir(job_id: str) -> None:
    """Safely removes the temporary directory and all files for a job."""
    try:
        job_dir = get_job_temp_dir(job_id)
        if job_dir.exists() and job_dir.is_dir():
            shutil.rmtree(job_dir, ignore_errors=True)
            logger.info(f"Cleaned up directory for job {job_id}")
    except Exception as e:
        logger.warning(f"Error cleaning up job directory {job_id}: {e}")

def get_file_size(file_path: str) -> Optional[int]:
    """Returns size in bytes of a file if it exists."""
    try:
        p = Path(file_path)
        if p.exists() and p.is_file():
            return p.stat().st_size
    except Exception:
        pass
    return None

def periodic_temp_cleanup() -> int:
    """
    Scans the base temp directory and removes folders older than JOB_RETENTION_SECONDS.
    Returns number of folders cleaned up.
    """
    cleaned_count = 0
    now = time.time()
    base_dir = Path(settings.BASE_TEMP_DIR)
    
    if not base_dir.exists():
        return 0
    
    try:
        for item in base_dir.iterdir():
            if item.is_dir():
                try:
                    # Check folder modification/creation time
                    mtime = item.stat().st_mtime
                    if now - mtime > settings.JOB_RETENTION_SECONDS:
                        shutil.rmtree(item, ignore_errors=True)
                        cleaned_count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove stale directory {item}: {e}")
    except Exception as e:
        logger.error(f"Error during periodic temp cleanup: {e}")
        
    return cleaned_count
