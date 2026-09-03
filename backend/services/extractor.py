import logging
from typing import Dict, Any, Optional, Callable
import yt_dlp

logger = logging.getLogger("mediaflow.extractor")

class ExtractorError(Exception):
    """Custom exception for extraction issues."""
    pass

class MediaRestrictedError(ExtractorError):
    """Exception when media is protected by DRM or access restrictions."""
    pass

def get_ydl_base_options() -> Dict[str, Any]:
    """Returns safe, secure default options for yt-dlp."""
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 20,
        "retries": 3,
        "nocheckcertificate": False,
        "prefer_insecure": False,
        "ignoreerrors": False,
        "geo_bypass": True,
        "extract_flat": False,
    }

def analyze_media_url(url: str) -> Dict[str, Any]:
    """
    Extracts metadata, stream formats, and audio information without downloading media.
    Catches DRM and access restriction errors gracefully.
    """
    opts = get_ydl_base_options()
    opts["skip_download"] = True
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise ExtractorError("No media stream information could be retrieved from this URL.")
            
            # If playlist returned, take first entry
            if "entries" in info:
                entries = list(info.get("entries", []))
                if entries and entries[0]:
                    info = entries[0]
                else:
                    raise ExtractorError("No media entries found.")
            
            return info
            
    except yt_dlp.utils.DownloadError as e:
        err_msg = str(e).lower()
        logger.warning(f"yt-dlp download error for {url}: {err_msg}")
        
        # Check for DRM / restricted patterns
        if any(keyword in err_msg for keyword in [
            "drm", "protected", "copyright", "sign in", "login", 
            "private", "members-only", "premium", "paywall", 
            "geographic", "blocked", "restricted", "token"
        ]):
            raise MediaRestrictedError(
                "This media cannot be processed because it is protected, restricted, or unavailable."
            )
        elif "unsupported url" in err_msg or "is not a valid url" in err_msg:
            raise ExtractorError("The provided URL is not a supported media source.")
        elif "video unavailable" in err_msg or "not found" in err_msg:
            raise ExtractorError("The requested media is unavailable or has been removed.")
        else:
            raise ExtractorError(f"Media extraction failed: {str(e)[:120]}")
            
    except Exception as e:
        logger.error(f"Unexpected error analyzing URL {url}: {e}")
        raise ExtractorError(f"Failed to analyze media URL: {str(e)}")

def download_media_stream(
    url: str,
    format_id: str,
    output_template: str,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> Dict[str, Any]:
    """
    Downloads the specified format stream to disk using yt-dlp.
    """
    opts = get_ydl_base_options()
    opts["format"] = format_id
    opts["outtmpl"] = output_template
    
    if progress_callback:
        opts["progress_hooks"] = [progress_callback]
        
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info
    except yt_dlp.utils.DownloadError as e:
        err_msg = str(e).lower()
        if any(keyword in err_msg for keyword in ["drm", "protected", "private", "sign in"]):
            raise MediaRestrictedError(
                "This media cannot be processed because it is protected, restricted, or unavailable."
            )
        raise ExtractorError(f"Download failed: {str(e)[:120]}")
    except Exception as e:
        raise ExtractorError(f"Stream download encountered an error: {str(e)}")
