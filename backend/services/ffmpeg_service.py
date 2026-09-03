import os
import re
import json
import shutil
import logging
import subprocess
from typing import Optional, Dict, Any, Callable

logger = logging.getLogger("mediaflow.ffmpeg")

_FFMPEG_INITIALIZED = False

def ensure_ffmpeg_initialized() -> bool:
    """Ensures ffmpeg and ffprobe are available in PATH via static_ffmpeg or system."""
    global _FFMPEG_INITIALIZED
    if _FFMPEG_INITIALIZED:
        return True
    
    # Check if system already has ffmpeg
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        _FFMPEG_INITIALIZED = True
        return True
    
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
        if shutil.which("ffmpeg") and shutil.which("ffprobe"):
            _FFMPEG_INITIALIZED = True
            logger.info("static_ffmpeg initialized successfully.")
            return True
    except Exception as e:
        logger.warning(f"Could not initialize static_ffmpeg: {e}")
    
    return shutil.which("ffmpeg") is not None

def get_ffmpeg_version() -> Optional[str]:
    """Retrieves the installed FFmpeg version."""
    ensure_ffmpeg_initialized()
    try:
        res = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5, check=False)
        if res.returncode == 0:
            lines = res.stdout.splitlines()
            return lines[0] if lines else "FFmpeg (version unknown)"
    except Exception as e:
        logger.warning(f"Failed to get ffmpeg version: {e}")
    return None

def get_ffprobe_version() -> Optional[str]:
    """Retrieves the installed FFprobe version."""
    ensure_ffmpeg_initialized()
    try:
        res = subprocess.run(["ffprobe", "-version"], capture_output=True, text=True, timeout=5, check=False)
        if res.returncode == 0:
            lines = res.stdout.splitlines()
            return lines[0] if lines else "FFprobe (version unknown)"
    except Exception as e:
        logger.warning(f"Failed to get ffprobe version: {e}")
    return None

def probe_media_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Probes a media file using ffprobe and returns json stream & format metadata."""
    ensure_ffmpeg_initialized()
    if not os.path.exists(file_path):
        return None
    
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path
    ]
    
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15, check=False)
        if res.returncode == 0 and res.stdout:
            return json.loads(res.stdout)
    except Exception as e:
        logger.error(f"Error probing file {file_path}: {e}")
    
    return None

def run_ffmpeg_command(
    args: list[str],
    total_duration_sec: Optional[float] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None,
    timeout_sec: int = 600
) -> bool:
    """
    Executes an FFmpeg command with safe argument array and tracks progress.
    progress_callback receives (percent: float, message: str)
    """
    ensure_ffmpeg_initialized()
    
    # Prepend 'ffmpeg' and '-y' for overwrite if not present
    cmd = ["ffmpeg", "-y"] + args
    logger.info(f"Running safe FFmpeg command: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        
        time_regex = re.compile(r"time=(\d+):(\d+):(\d+\.?\d*)")
        
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            
            if line and total_duration_sec and total_duration_sec > 0:
                match = time_regex.search(line)
                if match:
                    hours = float(match.group(1))
                    mins = float(match.group(2))
                    secs = float(match.group(3))
                    current_sec = hours * 3600 + mins * 60 + secs
                    pct = min(99.0, (current_sec / total_duration_sec) * 100.0)
                    if progress_callback:
                        progress_callback(pct, f"Processing media: {pct:.1f}%")
        
        returncode = process.wait(timeout=timeout_sec)
        if returncode != 0:
            stderr_out = process.stderr.read()
            logger.error(f"FFmpeg command failed with code {returncode}: {stderr_out}")
            return False
            
        if progress_callback:
            progress_callback(100.0, "Media processing complete.")
            
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"FFmpeg command timed out after {timeout_sec}s")
        try:
            process.kill()
        except Exception:
            pass
        return False
    except Exception as e:
        logger.error(f"Exception running FFmpeg: {e}")
        return False
