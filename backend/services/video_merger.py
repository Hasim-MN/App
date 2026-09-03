import os
import logging
from typing import Optional, Callable
from backend.services.ffmpeg_service import run_ffmpeg_command

logger = logging.getLogger("mediaflow.video_merger")

def merge_video_audio_streams(
    video_path: str,
    audio_path: str,
    output_path: str,
    target_container: str = "mp4",
    duration: Optional[float] = None,
    callback: Optional[Callable[[float, str], None]] = None
) -> bool:
    """
    Merges separate video and audio streams using FFmpeg.
    First tries fast stream copying (-c copy).
    If incompatible, falls back to safe remuxing/transcoding.
    """
    if callback:
        callback(50.0, "Merging video and audio streams...")
        
    # 1. First attempt: Stream Copy (-c copy)
    args_copy = [
        "-i", video_path,
        "-i", audio_path,
        "-c", "copy",
        "-shortest"
    ]
    
    if target_container == "mp4":
        args_copy.extend(["-movflags", "+faststart"])
        
    args_copy.append(output_path)
    
    success = run_ffmpeg_command(args_copy, total_duration_sec=duration, progress_callback=callback)
    if success and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        logger.info("Successfully merged streams using stream copy.")
        return True
    
    logger.warning("Stream copy merge failed or produced empty file. Retrying with compatibility transcode...")
    
    # Clean up empty output if failed
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except Exception:
            pass
            
    # 2. Fallback: Compatible transcode
    if target_container == "mp4":
        args_transcode = [
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-shortest",
            output_path
        ]
    elif target_container == "webm":
        args_transcode = [
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "libvpx-vp9",
            "-crf", "30",
            "-b:v", "0",
            "-c:a", "libopus",
            "-b:a", "160k",
            "-shortest",
            output_path
        ]
    else:  # mkv
        args_transcode = [
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]
        
    return run_ffmpeg_command(args_transcode, total_duration_sec=duration, progress_callback=callback)

def remux_video_container(
    input_path: str,
    output_path: str,
    target_container: str = "mp4",
    duration: Optional[float] = None,
    callback: Optional[Callable[[float, str], None]] = None
) -> bool:
    """Remuxes a single combined video file to another container."""
    args = ["-i", input_path, "-c", "copy"]
    if target_container == "mp4":
        args.extend(["-movflags", "+faststart"])
    args.append(output_path)
    return run_ffmpeg_command(args, total_duration_sec=duration, progress_callback=callback)
