from typing import Optional, List
from pydantic import BaseModel, Field

class VideoFormat(BaseModel):
    format_id: str
    extension: str
    quality_label: str
    resolution: str
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None
    bitrate_kbps: Optional[float] = None
    estimated_size_bytes: Optional[int] = None
    has_video: bool = True
    has_audio: bool = False
    is_dash_video: bool = False
    audio_format_id_for_merge: Optional[str] = None

class OriginalAudioSpecs(BaseModel):
    codec: str = "unknown"
    bitrate_kbps: Optional[float] = None
    sample_rate_hz: Optional[int] = None
    channels: Optional[int] = None
    channel_layout: Optional[str] = "Stereo"
    bit_depth: Optional[int] = None
    estimated_size_bytes: Optional[int] = None
    format_id: Optional[str] = None
    extension: Optional[str] = None

class AudioFormatOption(BaseModel):
    format: str
    name: str
    type: str  # "lossy" | "lossless" | "uncompressed"
    description: str
    recommended_quality: str
    default_extension: str

class MediaInfo(BaseModel):
    url: str
    title: str
    thumbnail: Optional[str] = None
    duration_seconds: Optional[float] = None
    duration_formatted: str = "00:00"
    source: str = "Supported Stream"
    uploader: Optional[str] = None
    view_count: Optional[int] = None
    upload_date: Optional[str] = None
    description: Optional[str] = None
    video_formats: List[VideoFormat] = Field(default_factory=list)
    original_audio: Optional[OriginalAudioSpecs] = None
    supported_audio_formats: List[AudioFormatOption] = Field(default_factory=list)
