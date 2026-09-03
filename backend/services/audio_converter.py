import os
import logging
from typing import Optional, Callable, List
from backend.services.ffmpeg_service import run_ffmpeg_command
from backend.models.requests import AudioDownloadRequest

logger = logging.getLogger("mediaflow.audio_converter")

# Predefined safe bitrates
VALID_BITRATES = {"64k", "96k", "128k", "160k", "192k", "256k", "320k"}
VALID_SAMPLE_RATES = {"44100", "48000", "88200", "96000", "192000"}
VALID_BIT_DEPTHS = {"16", "24", "32_float"}

def get_audio_filter_args(normalize: bool = False, channels: Optional[str] = None) -> List[str]:
    """Builds safe audio filter and channel configuration arguments."""
    args = []
    
    # Audio channels
    if channels == "mono":
        args.extend(["-ac", "1"])
    elif channels == "stereo":
        args.extend(["-ac", "2"])
        
    # Audio normalization filter
    if normalize:
        args.extend(["-af", "loudnorm=I=-16:TP=-1.5:LRA=11"])
        
    return args

def apply_sample_rate(args: List[str], sample_rate: Optional[str]) -> None:
    """Applies validated sample rate parameter."""
    if sample_rate and sample_rate != "original" and sample_rate in VALID_SAMPLE_RATES:
        args.extend(["-ar", sample_rate])

def convert_to_mp3(
    input_path: str,
    output_path: str,
    bitrate: str = "320k",
    sample_rate: str = "original",
    normalize: bool = False,
    channels: str = "original",
    duration: Optional[float] = None,
    callback: Optional[Callable[[float, str], None]] = None
) -> bool:
    """Converts audio to MP3 using libmp3lame."""
    safe_bitrate = bitrate if bitrate in VALID_BITRATES else "320k"
    args = ["-i", input_path, "-vn", "-c:a", "libmp3lame", "-b:a", safe_bitrate]
    args.extend(get_audio_filter_args(normalize, channels))
    apply_sample_rate(args, sample_rate)
    args.append(output_path)
    return run_ffmpeg_command(args, total_duration_sec=duration, progress_callback=callback)

def convert_to_flac(
    input_path: str,
    output_path: str,
    bit_depth: str = "original",
    sample_rate: str = "original",
    compression_level: int = 5,
    normalize: bool = False,
    channels: str = "original",
    duration: Optional[float] = None,
    callback: Optional[Callable[[float, str], None]] = None
) -> bool:
    """Converts audio to lossless FLAC."""
    comp = max(0, min(8, int(compression_level or 5)))
    args = ["-i", input_path, "-vn", "-c:a", "flac", "-compression_level", str(comp)]
    
    if bit_depth == "16":
        args.extend(["-sample_fmt", "s16"])
    elif bit_depth == "24":
        args.extend(["-sample_fmt", "s32"])  # standard 24/32bit container for FLAC
        
    args.extend(get_audio_filter_args(normalize, channels))
    apply_sample_rate(args, sample_rate)
    args.append(output_path)
    return run_ffmpeg_command(args, total_duration_sec=duration, progress_callback=callback)

def convert_to_wav(
    input_path: str,
    output_path: str,
    bit_depth: str = "24",
    sample_rate: str = "original",
    normalize: bool = False,
    channels: str = "original",
    duration: Optional[float] = None,
    callback: Optional[Callable[[float, str], None]] = None
) -> bool:
    """Converts audio to uncompressed studio PCM WAV."""
    if bit_depth == "16":
        pcm_codec = "pcm_s16le"
    elif bit_depth == "32_float":
        pcm_codec = "pcm_f32le"
    else:
        pcm_codec = "pcm_s24le"  # default 24-bit PCM
        
    args = ["-i", input_path, "-vn", "-c:a", pcm_codec]
    args.extend(get_audio_filter_args(normalize, channels))
    apply_sample_rate(args, sample_rate)
    args.append(output_path)
    return run_ffmpeg_command(args, total_duration_sec=duration, progress_callback=callback)

def convert_to_aac(
    input_path: str,
    output_path: str,
    bitrate: str = "256k",
    sample_rate: str = "original",
    normalize: bool = False,
    channels: str = "original",
    duration: Optional[float] = None,
    callback: Optional[Callable[[float, str], None]] = None
) -> bool:
    """Converts audio to raw AAC."""
    safe_bitrate = bitrate if bitrate in VALID_BITRATES else "256k"
    args = ["-i", input_path, "-vn", "-c:a", "aac", "-b:a", safe_bitrate]
    args.extend(get_audio_filter_args(normalize, channels))
    apply_sample_rate(args, sample_rate)
    args.append(output_path)
    return run_ffmpeg_command(args, total_duration_sec=duration, progress_callback=callback)

def convert_to_m4a(
    input_path: str,
    output_path: str,
    bitrate: str = "256k",
    sample_rate: str = "original",
    normalize: bool = False,
    channels: str = "original",
    duration: Optional[float] = None,
    callback: Optional[Callable[[float, str], None]] = None
) -> bool:
    """Converts audio to AAC inside M4A container with faststart."""
    safe_bitrate = bitrate if bitrate in VALID_BITRATES else "256k"
    args = ["-i", input_path, "-vn", "-c:a", "aac", "-b:a", safe_bitrate, "-movflags", "+faststart"]
    args.extend(get_audio_filter_args(normalize, channels))
    apply_sample_rate(args, sample_rate)
    args.append(output_path)
    return run_ffmpeg_command(args, total_duration_sec=duration, progress_callback=callback)

def convert_to_ogg(
    input_path: str,
    output_path: str,
    quality: int = 5,
    sample_rate: str = "original",
    normalize: bool = False,
    channels: str = "original",
    duration: Optional[float] = None,
    callback: Optional[Callable[[float, str], None]] = None
) -> bool:
    """Converts audio to Ogg Vorbis with variable quality level 0-10."""
    q = max(0, min(10, int(quality if quality is not None else 5)))
    args = ["-i", input_path, "-vn", "-c:a", "libvorbis", "-q:a", str(q)]
    args.extend(get_audio_filter_args(normalize, channels))
    apply_sample_rate(args, sample_rate)
    args.append(output_path)
    return run_ffmpeg_command(args, total_duration_sec=duration, progress_callback=callback)

def convert_to_opus(
    input_path: str,
    output_path: str,
    bitrate: str = "160k",
    sample_rate: str = "original",
    normalize: bool = False,
    channels: str = "original",
    duration: Optional[float] = None,
    callback: Optional[Callable[[float, str], None]] = None
) -> bool:
    """Converts audio to OPUS."""
    safe_bitrate = bitrate if bitrate in VALID_BITRATES else "160k"
    args = ["-i", input_path, "-vn", "-c:a", "libopus", "-b:a", safe_bitrate]
    args.extend(get_audio_filter_args(normalize, channels))
    apply_sample_rate(args, sample_rate)
    args.append(output_path)
    return run_ffmpeg_command(args, total_duration_sec=duration, progress_callback=callback)

def convert_to_alac(
    input_path: str,
    output_path: str,
    bit_depth: str = "original",
    sample_rate: str = "original",
    normalize: bool = False,
    channels: str = "original",
    duration: Optional[float] = None,
    callback: Optional[Callable[[float, str], None]] = None
) -> bool:
    """Converts audio to Apple Lossless Audio Codec (ALAC in m4a container)."""
    args = ["-i", input_path, "-vn", "-c:a", "alac"]
    if bit_depth == "16":
        args.extend(["-sample_fmt", "s16p"])
    elif bit_depth == "24":
        args.extend(["-sample_fmt", "s32p"])
        
    args.extend(get_audio_filter_args(normalize, channels))
    apply_sample_rate(args, sample_rate)
    args.append(output_path)
    return run_ffmpeg_command(args, total_duration_sec=duration, progress_callback=callback)

def convert_to_aiff(
    input_path: str,
    output_path: str,
    bit_depth: str = "24",
    sample_rate: str = "original",
    normalize: bool = False,
    channels: str = "original",
    duration: Optional[float] = None,
    callback: Optional[Callable[[float, str], None]] = None
) -> bool:
    """Converts audio to AIFF PCM."""
    if bit_depth == "16":
        pcm_codec = "pcm_s16be"
    elif bit_depth == "32_float":
        pcm_codec = "pcm_f32be"
    else:
        pcm_codec = "pcm_s24be"
        
    args = ["-i", input_path, "-vn", "-c:a", pcm_codec]
    args.extend(get_audio_filter_args(normalize, channels))
    apply_sample_rate(args, sample_rate)
    args.append(output_path)
    return run_ffmpeg_command(args, total_duration_sec=duration, progress_callback=callback)

def extract_original_audio(
    input_path: str,
    output_path: str,
    duration: Optional[float] = None,
    callback: Optional[Callable[[float, str], None]] = None
) -> bool:
    """Extracts original audio stream with zero transcoding (stream copy)."""
    args = ["-i", input_path, "-vn", "-c:a", "copy", output_path]
    return run_ffmpeg_command(args, total_duration_sec=duration, progress_callback=callback)

def process_audio_conversion(
    input_path: str,
    output_path: str,
    req: AudioDownloadRequest,
    duration: Optional[float] = None,
    callback: Optional[Callable[[float, str], None]] = None
) -> bool:
    """
    Routes the audio conversion request to the appropriate format handler.
    """
    fmt = req.format.lower()
    
    if fmt == "original":
        return extract_original_audio(input_path, output_path, duration, callback)
    elif fmt == "mp3":
        return convert_to_mp3(
            input_path, output_path,
            bitrate=req.quality_bitrate or "320k",
            sample_rate=req.sample_rate or "original",
            normalize=bool(req.normalize_audio),
            channels=req.channels or "original",
            duration=duration, callback=callback
        )
    elif fmt == "flac":
        return convert_to_flac(
            input_path, output_path,
            bit_depth=req.bit_depth or "original",
            sample_rate=req.sample_rate or "original",
            compression_level=req.compression_level if req.compression_level is not None else 5,
            normalize=bool(req.normalize_audio),
            channels=req.channels or "original",
            duration=duration, callback=callback
        )
    elif fmt == "wav":
        return convert_to_wav(
            input_path, output_path,
            bit_depth=req.bit_depth or "24",
            sample_rate=req.sample_rate or "original",
            normalize=bool(req.normalize_audio),
            channels=req.channels or "original",
            duration=duration, callback=callback
        )
    elif fmt == "m4a":
        return convert_to_m4a(
            input_path, output_path,
            bitrate=req.quality_bitrate or "256k",
            sample_rate=req.sample_rate or "original",
            normalize=bool(req.normalize_audio),
            channels=req.channels or "original",
            duration=duration, callback=callback
        )
    elif fmt == "aac":
        return convert_to_aac(
            input_path, output_path,
            bitrate=req.quality_bitrate or "256k",
            sample_rate=req.sample_rate or "original",
            normalize=bool(req.normalize_audio),
            channels=req.channels or "original",
            duration=duration, callback=callback
        )
    elif fmt == "ogg":
        return convert_to_ogg(
            input_path, output_path,
            quality=req.ogg_quality if req.ogg_quality is not None else 5,
            sample_rate=req.sample_rate or "original",
            normalize=bool(req.normalize_audio),
            channels=req.channels or "original",
            duration=duration, callback=callback
        )
    elif fmt == "opus":
        return convert_to_opus(
            input_path, output_path,
            bitrate=req.quality_bitrate or "160k",
            sample_rate=req.sample_rate or "original",
            normalize=bool(req.normalize_audio),
            channels=req.channels or "original",
            duration=duration, callback=callback
        )
    elif fmt == "alac":
        return convert_to_alac(
            input_path, output_path,
            bit_depth=req.bit_depth or "original",
            sample_rate=req.sample_rate or "original",
            normalize=bool(req.normalize_audio),
            channels=req.channels or "original",
            duration=duration, callback=callback
        )
    elif fmt == "aiff":
        return convert_to_aiff(
            input_path, output_path,
            bit_depth=req.bit_depth or "24",
            sample_rate=req.sample_rate or "original",
            normalize=bool(req.normalize_audio),
            channels=req.channels or "original",
            duration=duration, callback=callback
        )
    else:
        # Default fallback to MP3
        return convert_to_mp3(input_path, output_path, duration=duration, callback=callback)
