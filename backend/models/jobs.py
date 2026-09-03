import time
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PREPARING = "PREPARING"
    DOWNLOADING = "DOWNLOADING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class JobProgress(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.QUEUED
    phase: str = "Preparing media..."
    percent: float = 0.0
    speed_str: Optional[str] = None
    eta_str: Optional[str] = None
    downloaded_bytes: Optional[int] = None
    total_bytes: Optional[int] = None
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    media_title: Optional[str] = None
    media_thumbnail: Optional[str] = None
    selected_format: Optional[str] = None
    output_path: Optional[str] = None
    error: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    download_url: Optional[str] = None

class JobHistoryItem(BaseModel):
    job_id: str
    title: str
    thumbnail: Optional[str] = None
    format_type: str
    selected_quality: str
    file_size_bytes: Optional[int] = None
    completed_at: float
    file_name: str
