import logging
from typing import Dict, Any, Optional, Callable
import yt_dlp

import os
from pathlib import Path
from backend.services.ffmpeg_service import get_ffmpeg_dir

logger = logging.getLogger("mediaflow.extractor")

class ExtractorError(Exception):
    """Custom exception for extraction issues."""
    pass

class MediaRestrictedError(ExtractorError):
    """Exception when media is protected by DRM or access restrictions."""
    pass

def get_ydl_base_options() -> Dict[str, Any]:
    """Returns safe, secure default options for yt-dlp with Windows filesystem resilience and anti-bot bypass."""
    opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 25,
        "retries": 3,
        "nocheckcertificate": False,
        "prefer_insecure": False,
        "ignoreerrors": False,
        "geo_bypass": True,
        "extract_flat": False,
        # Windows & OS file system resilience
        "windowsfilenames": True,
        "restrictfilenames": True,
        "trim_file_name": 100,
        "updatetime": False,       # Prevents Windows os.utime [Errno 22] Invalid argument
        "no_mtime": True,
        "overwrites": True,
        "no_color": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    # Bind JS Runtime (Node.js or Deno) for YouTube signature deciphering
    import shutil
    if shutil.which("node"):
        opts["js_runtimes"] = {"node": {}}
    elif shutil.which("deno"):
        opts["js_runtimes"] = {"deno": {}}

    # Bind cookies if passed via environment variable (useful for Render/Cloud hosts)
    raw_cookies = (
        os.environ.get("YOUTUBE_COOKIES") or 
        os.environ.get("YOUTUBE_COOKIE") or 
        os.environ.get("COOKIES") or 
        os.environ.get("COOKIE") or 
        os.environ.get("COOKIES_DATA") or
        os.environ.get("COOKIES_TEXT")
    )
    if raw_cookies and raw_cookies.strip():
        import tempfile
        import base64
        data = raw_cookies.strip()
        # Strip wrapping quotes if user pasted with quotes
        if (data.startswith('"') and data.endswith('"')) or (data.startswith("'") and data.endswith("'")):
            data = data[1:-1].strip()
        if "\\n" in data and "\n" not in data:
            data = data.replace("\\n", "\n").replace("\\t", "\t")
        try:
            if not ("# Netscape" in data or "\t" in data) and len(data) > 20:
                data = base64.b64decode(data).decode("utf-8")
        except Exception:
            pass
        if not data.startswith("#"):
            data = "# Netscape HTTP Cookie File\n" + data
            
        cookie_path = os.path.join(tempfile.gettempdir(), "mediaflow_yt_cookies.txt")
        try:
            with open(cookie_path, "w", encoding="utf-8") as f:
                f.write(data)
            opts["cookiefile"] = cookie_path
            logger.info(f"Loaded {len(data)} bytes of YouTube cookies into {cookie_path}")
        except Exception as e:
            logger.warning(f"Could not write YOUTUBE_COOKIES to temp file: {e}")
    else:
        cookie_file = os.environ.get("COOKIES_FILE") or os.environ.get("YOUTUBE_COOKIES_FILE")
        if cookie_file and os.path.exists(cookie_file):
            opts["cookiefile"] = cookie_file
        elif os.path.exists("cookies.txt"):
            opts["cookiefile"] = "cookies.txt"

    # Bind proxy if configured
    proxy = os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY")
    if proxy:
        opts["proxy"] = proxy

    # Bind FFmpeg location if available
    try:
        ffmpeg_dir = get_ffmpeg_dir()
        if ffmpeg_dir:
            opts["ffmpeg_location"] = ffmpeg_dir
    except Exception as e:
        logger.debug(f"Could not bind ffmpeg_location in yt-dlp: {e}")

    return opts

def analyze_media_url(url: str) -> Dict[str, Any]:
    """
    Extracts metadata, stream formats, and audio information without downloading media.
    Catches DRM and access restriction errors gracefully.
    """
    opts = get_ydl_base_options()
    opts["skip_download"] = True
    opts["check_formats"] = False
    
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
        
        # Check for datacenter / bot block patterns
        if "failed to extract any player response" in err_msg or "confirm you're not a bot" in err_msg:
            raise ExtractorError(
                f"YouTube anti-bot block on cloud server: {str(e)[:160]}"
            )
        # Check for DRM / restricted patterns
        elif any(keyword in err_msg for keyword in [
            "drm", "protected", "copyright", "sign in", "login", 
            "private", "members-only", "premium", "paywall", 
            "geographic", "blocked", "restricted"
        ]):
            raise MediaRestrictedError(
                f"Media restricted: {str(e)[:180]}"
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
    Downloads the specified format stream to disk using yt-dlp with Windows safe paths.
    """
    opts = get_ydl_base_options()
    
    # Isolate directory and filename to prevent backslash/path concatenation bugs on Windows
    out_path = Path(output_template)
    job_dir = str(out_path.parent.resolve())
    file_name_tmpl = out_path.name

    opts["paths"] = {"home": job_dir, "temp": job_dir}
    opts["outtmpl"] = {"default": file_name_tmpl}
    
    # Resilient format selector: prioritize requested format_id with safe fallbacks
    if format_id and format_id.strip() and format_id.strip().lower() not in ("none", "null", "undefined"):
        clean_fid = format_id.strip()
        opts["format"] = f"{clean_fid}/bestvideo+bestaudio/bestaudio/best"
    else:
        opts["format"] = "bestvideo+bestaudio/bestaudio/best"
    
    if progress_callback:
        opts["progress_hooks"] = [progress_callback]
        
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info
    except yt_dlp.utils.DownloadError as e:
        err_msg = str(e).lower()
        if "failed to extract any player response" in err_msg or "confirm you're not a bot" in err_msg:
            raise ExtractorError(
                "YouTube anti-bot block detected on this server IP. "
                "Connect your mobile app to your Local PC server (http://<PC-IP>:8000) on the same Wi-Fi."
            )
        if any(keyword in err_msg for keyword in ["drm", "protected", "private", "sign in"]):
            raise MediaRestrictedError(
                "This media cannot be processed because it is protected, restricted, or unavailable."
            )
        raise ExtractorError(f"Download failed: {str(e)[:120]}")
    except yt_dlp.utils.UnavailableVideoError as e:
        err_str = str(e)
        logger.error(f"UnavailableVideoError downloading {url}: {err_str}")
        if "errno 22" in err_str.lower():
            raise ExtractorError("File system error: filename or stream parameters could not be written to disk.")
        raise ExtractorError(f"Media stream unavailable: {err_str[:120]}")
    except yt_dlp.utils.YoutubeDLError as e:
        logger.error(f"YoutubeDLError downloading {url}: {e}")
        raise ExtractorError(f"Stream download error: {str(e)[:120]}")
    except Exception as e:
        err_str = str(e)
        logger.error(f"Unexpected error downloading stream: {err_str}")
        if "errno 22" in err_str.lower():
            raise ExtractorError("Storage write error: invalid file argument or path restriction.")
        raise ExtractorError(f"Stream download encountered an error: {err_str[:120]}")
