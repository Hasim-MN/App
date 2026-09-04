import logging
from typing import Dict, Any, List, Optional
from backend.models.media import MediaInfo, VideoFormat, OriginalAudioSpecs, AudioFormatOption

logger = logging.getLogger("mediaflow.analyzer")

SUPPORTED_AUDIO_FORMATS = [
    AudioFormatOption(
        format="mp3",
        name="MP3",
        type="lossy",
        description="Lossy audio with universal device compatibility.",
        recommended_quality="320 kbps",
        default_extension="mp3"
    ),
    AudioFormatOption(
        format="flac",
        name="FLAC",
        type="lossless",
        description="Lossless compression preserving full master audio quality.",
        recommended_quality="Lossless",
        default_extension="flac"
    ),
    AudioFormatOption(
        format="wav",
        name="WAV",
        type="uncompressed",
        description="Uncompressed studio PCM audio for pro editing.",
        recommended_quality="24-bit PCM",
        default_extension="wav"
    ),
    AudioFormatOption(
        format="m4a",
        name="M4A",
        type="lossy",
        description="AAC in M4A container with superior mobile compression.",
        recommended_quality="256 kbps",
        default_extension="m4a"
    ),
    AudioFormatOption(
        format="aac",
        name="AAC",
        type="lossy",
        description="Advanced Audio Coding for high efficiency.",
        recommended_quality="256 kbps",
        default_extension="aac"
    ),
    AudioFormatOption(
        format="ogg",
        name="OGG",
        type="lossy",
        description="Open-source Vorbis audio format.",
        recommended_quality="Q7 — Very High",
        default_extension="ogg"
    ),
    AudioFormatOption(
        format="opus",
        name="OPUS",
        type="lossy",
        description="Next-generation ultra-efficient speech and music codec.",
        recommended_quality="160 kbps",
        default_extension="opus"
    ),
    AudioFormatOption(
        format="alac",
        name="ALAC",
        type="lossless",
        description="Apple Lossless Audio Codec for iOS and macOS.",
        recommended_quality="Lossless",
        default_extension="m4a"
    ),
    AudioFormatOption(
        format="aiff",
        name="AIFF",
        type="uncompressed",
        description="Uncompressed audio interchange file format.",
        recommended_quality="24-bit PCM",
        default_extension="aiff"
    ),
]

def format_duration(seconds: Optional[float]) -> str:
    """Formats duration in seconds into HH:MM:SS or MM:SS."""
    if not seconds or seconds < 0:
        return "00:00"
    
    total_sec = int(seconds)
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    secs = total_sec % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def clean_codec_name(raw_codec: Optional[str]) -> Optional[str]:
    """Cleans up raw yt-dlp codec names into readable descriptions."""
    if not raw_codec or raw_codec == "none":
        return None
    
    codec = raw_codec.lower()
    if "avc1" in codec or "h264" in codec or "h.264" in codec:
        return "H.264"
    elif "h265" in codec or "hevc" in codec or "hev1" in codec:
        return "H.265 / HEVC"
    elif "vp9" in codec or "vp09" in codec:
        return "VP9"
    elif "av01" in codec or "av1" in codec:
        return "AV1"
    elif "mp4a" in codec or "aac" in codec:
        return "AAC"
    elif "opus" in codec:
        return "Opus"
    elif "vorbis" in codec:
        return "Vorbis"
    elif "mp3" in codec:
        return "MP3"
    elif "flac" in codec:
        return "FLAC"
    
    return raw_codec.split(".")[0].upper()

def get_quality_label(height: int, fps: Optional[float] = None) -> str:
    """Returns standardized resolution label."""
    if height >= 4320:
        return "4320p 8K"
    elif height >= 2160:
        return "2160p 4K"
    elif height >= 1440:
        return "1440p 2K"
    elif height >= 1080:
        return "1080p Full HD"
    elif height >= 720:
        return "720p HD"
    elif height >= 480:
        return "480p"
    elif height >= 360:
        return "360p"
    elif height >= 240:
        return "240p"
    elif height >= 144:
        return "144p"
    return f"{height}p"

def parse_media_info(raw_info: Dict[str, Any], original_url: str) -> MediaInfo:
    """
    Parses raw yt-dlp dictionary into a clean, strongly typed MediaInfo object.
    """
    duration = raw_info.get("duration")
    raw_formats = raw_info.get("formats", [])
    
    # 1. Detect best audio stream
    audio_streams = []
    for f in raw_formats:
        acodec = f.get("acodec")
        vcodec = f.get("vcodec")
        if acodec and acodec != "none" and (not vcodec or vcodec == "none"):
            audio_streams.append(f)
    
    # Sort audio streams by bitrate descending
    audio_streams.sort(key=lambda x: x.get("abr") or x.get("tbr") or 0, reverse=True)
    best_audio_stream = audio_streams[0] if audio_streams else None
    
    # Also check if any format has combined audio
    if not best_audio_stream:
        combined_with_audio = [f for f in raw_formats if f.get("acodec") and f.get("acodec") != "none"]
        combined_with_audio.sort(key=lambda x: x.get("abr") or x.get("tbr") or 0, reverse=True)
        if combined_with_audio:
            best_audio_stream = combined_with_audio[0]

    original_audio_specs: Optional[OriginalAudioSpecs] = None
    if best_audio_stream:
        abr = best_audio_stream.get("abr") or best_audio_stream.get("tbr")
        asr = best_audio_stream.get("asr")
        acodec = clean_codec_name(best_audio_stream.get("acodec")) or "AAC"
        
        # Estimate size
        filesize = best_audio_stream.get("filesize") or best_audio_stream.get("filesize_approx")
        if not filesize and abr and duration:
            filesize = int((abr * 1000 / 8) * duration)
            
        original_audio_specs = OriginalAudioSpecs(
            codec=acodec,
            bitrate_kbps=float(abr) if abr else None,
            sample_rate_hz=int(asr) if asr else 48000,
            channels=best_audio_stream.get("audio_channels") or 2,
            channel_layout="Stereo" if (best_audio_stream.get("audio_channels") or 2) >= 2 else "Mono",
            estimated_size_bytes=filesize,
            format_id=str(best_audio_stream.get("format_id")),
            extension=best_audio_stream.get("ext", "m4a")
        )
    
    # 2. Parse and group video formats
    video_formats_map: Dict[str, VideoFormat] = {}
    best_audio_id = str(best_audio_stream.get("format_id")) if best_audio_stream else None
    
    import re
    for f in raw_formats:
        vcodec = f.get("vcodec")
        if (not vcodec or vcodec == "none") and f.get("video_ext") and f.get("video_ext") != "none":
            vcodec = f.get("video_ext")
        if not vcodec or vcodec == "none":
            continue
        
        height = f.get("height")
        width = f.get("width")
        if not height or height <= 0:
            res_str = str(f.get("resolution") or f.get("format_note") or "")
            m = re.search(r"(\d{3,4})p?", res_str)
            if m:
                try:
                    height = int(m.group(1))
                except ValueError:
                    height = 720
            else:
                height = 720
            
        acodec = f.get("acodec")
        has_audio = bool(acodec and acodec != "none")
        fps = f.get("fps")
        tbr = f.get("tbr") or f.get("vbr")
        ext = f.get("ext", "mp4")
        
        # Calculate size
        filesize = f.get("filesize") or f.get("filesize_approx")
        if not filesize and tbr and duration:
            audio_bitrate = (original_audio_specs.bitrate_kbps if original_audio_specs else 128) if not has_audio else 0
            filesize = int(((tbr + audio_bitrate) * 1000 / 8) * duration)
            
        q_label = get_quality_label(height, fps)
        v_codec_clean = clean_codec_name(vcodec) or "H.264"
        a_codec_clean = clean_codec_name(acodec) if has_audio else (original_audio_specs.codec if original_audio_specs else "AAC")
        
        # Create key to deduplicate identical resolution/codec pairs
        key = f"{height}_{fps}_{ext}_{v_codec_clean}"
        
        if key in video_formats_map:
            existing = video_formats_map[key]
            if (tbr or 0) <= (existing.bitrate_kbps or 0):
                continue
                
        video_format = VideoFormat(
            format_id=str(f.get("format_id")),
            extension=ext,
            quality_label=q_label,
            resolution=f"{width}x{height}" if width and height else f"{height}p",
            width=width,
            height=height,
            fps=fps,
            video_codec=v_codec_clean,
            audio_codec=a_codec_clean,
            bitrate_kbps=float(tbr) if tbr else None,
            estimated_size_bytes=filesize,
            has_video=True,
            has_audio=has_audio,
            is_dash_video=(not has_audio),
            audio_format_id_for_merge=best_audio_id if (not has_audio) else None
        )
        video_formats_map[key] = video_format

    # Fallback: if no video formats were parsed (common on datacenter IPs), provide smart defaults
    if not video_formats_map:
        logger.info(f"Using smart fallback formats for {original_url}")
        video_formats_map["1080"] = VideoFormat(
            format_id="bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            extension="mp4",
            quality_label="1080p Full HD",
            resolution="1920x1080",
            width=1920,
            height=1080,
            fps=30.0,
            video_codec="H.264",
            audio_codec="AAC",
            has_video=True,
            has_audio=True,
            is_dash_video=False
        )
        video_formats_map["720"] = VideoFormat(
            format_id="bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            extension="mp4",
            quality_label="720p HD",
            resolution="1280x720",
            width=1280,
            height=720,
            fps=30.0,
            video_codec="H.264",
            audio_codec="AAC",
            has_video=True,
            has_audio=True,
            is_dash_video=False
        )
        video_formats_map["360"] = VideoFormat(
            format_id="bestvideo[height<=360]+bestaudio/best[height<=360]/best",
            extension="mp4",
            quality_label="360p",
            resolution="640x360",
            width=640,
            height=360,
            fps=30.0,
            video_codec="H.264",
            audio_codec="AAC",
            has_video=True,
            has_audio=True,
            is_dash_video=False
        )

    # Fallback: ensure original_audio_specs is ALWAYS populated so audio conversion never fails
    if not original_audio_specs:
        original_audio_specs = OriginalAudioSpecs(
            codec="Opus/AAC",
            bitrate_kbps=160.0,
            sample_rate_hz=48000,
            channels=2,
            channel_layout="Stereo",
            format_id="bestaudio/best",
            extension="m4a"
        )

    # Sort video formats by height descending, then fps descending, then bitrate
    sorted_formats = sorted(
        video_formats_map.values(),
        key=lambda v: (v.height or 0, v.fps or 0, v.bitrate_kbps or 0),
        reverse=True
    )
    
    # Extract source platform name
    extractor_key = raw_info.get("extractor_key") or raw_info.get("extractor") or "Web Stream"
    
    return MediaInfo(
        url=original_url,
        title=raw_info.get("title") or "Untitled Media",
        thumbnail=raw_info.get("thumbnail"),
        duration_seconds=duration,
        duration_formatted=format_duration(duration),
        source=extractor_key,
        uploader=raw_info.get("uploader") or raw_info.get("channel"),
        view_count=raw_info.get("view_count"),
        upload_date=raw_info.get("upload_date"),
        description=raw_info.get("description")[:300] if raw_info.get("description") else None,
        video_formats=sorted_formats,
        original_audio=original_audio_specs,
        supported_audio_formats=SUPPORTED_AUDIO_FORMATS
    )
