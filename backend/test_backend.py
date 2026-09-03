import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.security import validate_url_security, sanitize_filename
from backend.services.ffmpeg_service import ensure_ffmpeg_initialized, get_ffmpeg_version
from backend.services.media_analyzer import get_quality_label, clean_codec_name, format_duration
from backend.models.requests import AudioDownloadRequest
from backend.services.audio_converter import process_audio_conversion

def test_security():
    print("=== Testing Security & SSRF Protection ===")
    
    # Blocked URLs
    blocked_urls = [
        "http://localhost:8000",
        "http://127.0.0.1:8000/secret",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/admin",
        "http://192.168.1.1/router",
        "http://172.16.0.5/internal",
        "file:///etc/passwd",
        "ftp://example.com/file",
        "gopher://evil.com",
        "javascript:alert(1)"
    ]
    for url in blocked_urls:
        valid, msg = validate_url_security(url)
        assert not valid, f"Expected {url} to be blocked! (Message: {msg})"
        print(f" [PASS] Blocked: {url} -> {msg}")
        
    # Safe Public URLs
    safe_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://vimeo.com/76979871",
        "https://soundcloud.com/artist/track"
    ]
    for url in safe_urls:
        valid, msg = validate_url_security(url)
        assert valid, f"Expected {url} to be allowed! (Error: {msg})"
        print(f" [PASS] Allowed: {url}")
        
    # Filename sanitization
    dirty = 'My Video: "Episode 1" <HD> / \\ | ? * .mp4'
    clean = sanitize_filename(dirty)
    print(f" [PASS] Sanitized: '{dirty}' -> '{clean}'")
    assert ":" not in clean and "<" not in clean and "/" not in clean

def test_ffmpeg_and_analyzer():
    print("\n=== Testing FFmpeg & Analyzer Helpers ===")
    ready = ensure_ffmpeg_initialized()
    assert ready, "FFmpeg initialization failed!"
    ver = get_ffmpeg_version()
    print(f" [PASS] FFmpeg Version: {ver}")
    
    assert format_duration(75) == "01:15"
    assert format_duration(3665) == "01:01:05"
    print(" [PASS] Duration formatter verified.")
    
    assert get_quality_label(1080) == "1080p Full HD"
    assert get_quality_label(2160) == "2160p 4K"
    assert get_quality_label(720) == "720p HD"
    print(" [PASS] Quality labels verified.")
    
    assert clean_codec_name("avc1.640028") == "H.264"
    assert clean_codec_name("vp09.00.51.08") == "VP9"
    assert clean_codec_name("mp4a.40.2") == "AAC"
    print(" [PASS] Codec names normalized.")

if __name__ == "__main__":
    test_security()
    test_ffmpeg_and_analyzer()
    print("\n>>> All Backend Unit Tests Passed Successfully! <<<")
