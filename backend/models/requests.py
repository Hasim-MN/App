from typing import Optional
from pydantic import BaseModel, Field

class AnalyzeRequest(BaseModel):
    url: str = Field(..., description="The URL of the media to analyze")

class VideoDownloadRequest(BaseModel):
    url: str = Field(..., description="The URL of the media")
    format_id: str = Field(..., description="Selected format_id or 'best'")
    container: str = Field(default="mp4", description="Desired container: mp4, webm, mkv")
    audio_format_id: Optional[str] = Field(default=None, description="Optional audio stream format_id to merge")
    title: Optional[str] = Field(default=None, description="Media title")
    thumbnail: Optional[str] = Field(default=None, description="Media thumbnail")

class AudioDownloadRequest(BaseModel):
    url: str = Field(..., description="The URL of the media")
    format: str = Field(default="mp3", description="Audio format: mp3, flac, wav, m4a, aac, ogg, opus, alac, aiff, original")
    quality_bitrate: Optional[str] = Field(default="320k", description="Bitrate for lossy formats: 64k, 96k, 128k, 160k, 192k, 256k, 320k, or vbr_high, vbr_med")
    ogg_quality: Optional[int] = Field(default=5, description="Vorbis quality level 0-10")
    sample_rate: Optional[str] = Field(default="original", description="Sample rate: original, 44100, 48000, 88200, 96000, 192000")
    bit_depth: Optional[str] = Field(default="original", description="Bit depth: original, 16, 24, 32_float")
    compression_level: Optional[int] = Field(default=5, description="FLAC compression level: 0-8")
    channels: Optional[str] = Field(default="original", description="Channels: original, mono, stereo")
    normalize_audio: Optional[bool] = Field(default=False, description="Apply EBU R128 loudness normalization")
    audio_format_id: Optional[str] = Field(default=None, description="Audio stream format_id if available")
    title: Optional[str] = Field(default=None, description="Media title")
    thumbnail: Optional[str] = Field(default=None, description="Media thumbnail")
