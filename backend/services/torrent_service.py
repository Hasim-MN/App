import os
import sys
import re
import shutil
import asyncio
import zipfile
import logging
import urllib.parse
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

from backend.models.media import MediaInfo, VideoFormat
from backend.utils.security import sanitize_filename

logger = logging.getLogger("mediaflow.torrent_service")

TORRENT_THUMBNAIL_DATA_URI = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 225' width='400' height='225'>"
    "<defs>"
    "<linearGradient id='bg' x1='0%' y1='0%' x2='100%' y2='100%'>"
    "<stop offset='0%' stop-color='%230f172a'/>"
    "<stop offset='50%' stop-color='%231e1b4b'/>"
    "<stop offset='100%' stop-color='%23083344'/>"
    "</linearGradient>"
    "<linearGradient id='grad' x1='0%' y1='0%' x2='100%' y2='100%'>"
    "<stop offset='0%' stop-color='%2306b6d4'/>"
    "<stop offset='100%' stop-color='%236366f1'/>"
    "</linearGradient>"
    "</defs>"
    "<rect width='400' height='225' rx='16' fill='url(%23bg)'/>"
    "<circle cx='200' cy='100' r='54' fill='%231e293b' stroke='%23334155' stroke-width='3'/>"
    "<path d='M180 80 C180 68, 220 68, 220 80 L220 105 C220 115, 200 115, 200 105 L200 85 C200 78, 200 78, 200 85 L200 105 C200 125, 240 125, 240 105 L240 80 C240 58, 160 58, 160 80 L160 110 C160 142, 210 142, 210 115' "
    "fill='none' stroke='url(%23grad)' stroke-width='10' stroke-linecap='round' stroke-linejoin='round'/>"
    "<text x='200' y='180' font-family='system-ui, sans-serif' font-size='20' font-weight='bold' fill='%23ffffff' text-anchor='middle'>BitTorrent P2P Swarm</text>"
    "<text x='200' y='202' font-family='system-ui, sans-serif' font-size='12' fill='%2394a3b8' text-anchor='middle'>High-Speed Magnet / Torrent Engine</text>"
    "</svg>"
)

def is_torrent_url(url: str) -> bool:
    """Checks whether a given URL is a BitTorrent magnet link or .torrent file URL."""
    if not url or not isinstance(url, str):
        return False
    clean = url.strip().lower()
    if clean.startswith("magnet:?"):
        return True
    try:
        parsed = urllib.parse.urlparse(clean)
        if parsed.path.endswith(".torrent") or ".torrent?" in clean:
            return True
    except Exception:
        pass
    return False

def get_aria2c_binary() -> Optional[str]:
    """
    Finds the aria2c static executable across platforms:
    - Standard PATH
    - Python Scripts / bin directories (installed by pip install aria2)
    - Custom ARIA2C_PATH environment variable
    """
    env_path = os.environ.get("ARIA2C_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    candidates = [
        shutil.which("aria2c"),
        os.path.join(sys.prefix, "Scripts", "aria2c.exe"),
        os.path.join(sys.prefix, "bin", "aria2c"),
        os.path.expanduser("~/.local/bin/aria2c"),
        r"C:\Users\alimd\AppData\Local\Python\pythoncore-3.14-64\Scripts\aria2c.exe",
        "/usr/bin/aria2c",
        "/usr/local/bin/aria2c",
    ]

    for cand in candidates:
        if cand and os.path.isfile(cand):
            return cand

    return None

def get_aria2c_version() -> Optional[str]:
    """Returns the version of aria2c if available."""
    bin_path = get_aria2c_binary()
    if not bin_path:
        return None
    try:
        import subprocess
        out = subprocess.check_output([bin_path, "--version"], text=True, stderr=subprocess.DEVNULL)
        first_line = out.splitlines()[0].strip()
        return first_line
    except Exception as e:
        logger.debug(f"Failed to query aria2c version: {e}")
        return None

def analyze_torrent_url(url: str) -> MediaInfo:
    """
    Parses metadata from a magnet URI or .torrent URL and produces a MediaInfo response.
    """
    url_clean = url.strip()
    title = "BitTorrent Media"
    info_hash = ""
    trackers: List[str] = []
    
    if url_clean.lower().startswith("magnet:?"):
        parsed = urllib.parse.urlparse(url_clean)
        qs = urllib.parse.parse_qs(parsed.query)
        
        # Extract display name (dn)
        dn_list = qs.get("dn", [])
        if dn_list and dn_list[0].strip():
            title = dn_list[0].strip()
            
        # Extract info hash
        xt_list = qs.get("xt", [])
        for xt in xt_list:
            if xt.lower().startswith("urn:btih:"):
                info_hash = xt[9:].strip()
                break
                
        if title == "BitTorrent Media" and info_hash:
            title = f"Torrent [{info_hash[:10]}]"
            
        trackers = qs.get("tr", [])
        source_label = "BitTorrent (Magnet Swarm)"
        desc = (
            f"BitTorrent P2P Magnet Link\n"
            f"InfoHash: {info_hash or 'Provided in link'}\n"
            f"Configured Trackers: {len(trackers)} tracker endpoints\n"
            f"Engine: aria2 multi-source DHT & PEX enabled"
        )
    else:
        # HTTP / HTTPS .torrent URL
        parsed = urllib.parse.urlparse(url_clean)
        path_name = os.path.basename(parsed.path)
        if path_name.lower().endswith(".torrent"):
            raw_title = path_name[:-8]
            title = raw_title.replace(".", " ").replace("-", " ").replace("_", " ").title()
        source_label = "BitTorrent (.torrent File)"
        desc = f"Direct BitTorrent file package: {path_name}"

    # Construct format option representing the torrent download
    formats = [
        VideoFormat(
            format_id="torrent_download",
            extension="zip",
            quality_label="BitTorrent P2P Package",
            resolution="High-Speed P2P",
            width=1920,
            height=1080,
            fps=30.0,
            video_codec="BitTorrent (DHT+PEX)",
            audio_codec="Original Media Streams",
            bitrate_kbps=None,
            estimated_size_bytes=None,
            has_video=True,
            has_audio=True,
            is_dash_video=False,
            audio_format_id_for_merge=None
        )
    ]

    return MediaInfo(
        url=url_clean,
        title=title,
        thumbnail=TORRENT_THUMBNAIL_DATA_URI,
        duration_seconds=None,
        duration_formatted="P2P Swarm",
        source=source_label,
        uploader=f"P2P Swarm ({len(trackers)} trackers)" if trackers else "Distributed P2P Swarm",
        view_count=None,
        upload_date=None,
        description=desc,
        video_formats=formats,
        original_audio=None,
        supported_audio_formats=[]
    )

async def run_torrent_download(
    job_id: str,
    url: str,
    job_dir: Path,
    update_callback
) -> Tuple[str, str, int]:
    """
    Executes an aria2c BitTorrent download job inside job_dir.
    Streams real-time progress via update_callback.
    Returns (final_output_path, final_filename, file_size_bytes).
    """
    bin_path = get_aria2c_binary()
    if not bin_path:
        raise RuntimeError("aria2c executable not found. Please verify that 'aria2' is installed.")

    logger.info(f"Starting aria2c torrent download for job {job_id} using {bin_path}")

    # Build aria2c command
    cmd = [
        bin_path,
        f"--dir={str(job_dir)}",
        "--seed-time=0",
        "--summary-interval=1",
        "--enable-dht=true",
        "--bt-enable-lpd=true",
        "--max-connection-per-server=16",
        "--bt-max-peers=60",
        "--file-allocation=none",
        "--auto-file-renaming=false",
        "--allow-overwrite=true",
        "--bt-stop-timeout=600",
        url
    ]

    await update_callback(
        status="DOWNLOADING",
        phase="Connecting to BitTorrent peers & resolving DHT metadata...",
        percent=5.0,
        speed="Connecting...",
        eta="Calculating..."
    )

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )

    # Regex for aria2c progress output line:
    # Example: [#2089b0 12MiB/120MiB(10%) CN:3 SD:5 DL:1.2MiB ETA:1m30s]
    progress_regex = re.compile(
        r"\[#\w+\s+([^\s/]+)/([^\s\(]+)\((\d+)%\).*?CN:(\d+).*?DL:([^\s]+)(?:.*?ETA:(\S+))?\]"
    )

    try:
        while True:
            line_bytes = await proc.stdout.readline()
            if not line_bytes:
                break
            line = line_bytes.decode(errors="replace").strip()
            if not line:
                continue

            match = progress_regex.search(line)
            if match:
                downloaded_str, total_str, pct_str, peers_str, speed_str, eta_str = match.groups()
                try:
                    pct = float(pct_str)
                except ValueError:
                    pct = 5.0

                capped_pct = min(99.0, max(5.0, pct))
                phase_text = f"Downloading torrent: {downloaded_str} of {total_str} ({pct:.0f}%)"
                speed_text = f"{speed_str} ({peers_str} peers)"
                eta_text = eta_str if eta_str else "calculating..."

                await update_callback(
                    status="DOWNLOADING",
                    phase=phase_text,
                    percent=capped_pct,
                    speed=speed_text,
                    eta=eta_text
                )
            elif "Download complete:" in line or "Download Results:" in line:
                await update_callback(
                    status="PROCESSING",
                    phase="Finalizing downloaded torrent files...",
                    percent=99.0,
                    speed="Finalizing...",
                    eta="0s"
                )

        await proc.wait()
    except asyncio.CancelledError:
        try:
            proc.terminate()
            await proc.wait()
        except Exception:
            pass
        raise

    if proc.returncode != 0:
        raise RuntimeError(f"BitTorrent download failed with exit code {proc.returncode}.")

    # Locate downloaded payload files (excluding .aria2 control files)
    downloaded_items = []
    for item in job_dir.iterdir():
        if item.name.endswith(".aria2"):
            try:
                item.unlink()
            except Exception:
                pass
            continue
        downloaded_items.append(item)

    if not downloaded_items:
        raise RuntimeError("No files were found in torrent output directory after download.")

    # If single file directly in job_dir
    if len(downloaded_items) == 1 and downloaded_items[0].is_file():
        final_file = downloaded_items[0]
        final_path = str(final_file)
        final_name = final_file.name
        file_size = final_file.stat().st_size
        return final_path, final_name, file_size

    # If single directory containing files or multiple files: create a clean zip
    target_zip = job_dir / "torrent_download.zip"
    total_size = 0

    with zipfile.ZipFile(target_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in downloaded_items:
            if item.is_file():
                zf.write(item, arcname=item.name)
                total_size += item.stat().st_size
            elif item.is_dir():
                for root, _, files in os.walk(item):
                    for file in files:
                        full_path = Path(root) / file
                        rel_path = full_path.relative_to(job_dir)
                        zf.write(full_path, arcname=str(rel_path))
                        total_size += full_path.stat().st_size

    final_path = str(target_zip)
    final_name = "torrent_package.zip"
    file_size = target_zip.stat().st_size

    return final_path, final_name, file_size
