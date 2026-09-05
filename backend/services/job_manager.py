import os
import shutil
import time
import uuid
import asyncio
import logging
from typing import Dict, List, Optional, AsyncGenerator
from backend.models.jobs import JobStatus, JobProgress, JobHistoryItem
from backend.models.requests import VideoDownloadRequest, AudioDownloadRequest
from backend.utils.files import get_job_temp_dir, cleanup_job_dir, get_file_size
from backend.utils.security import sanitize_filename
from backend.services.extractor import (
    analyze_media_url, download_media_stream, ExtractorError, MediaRestrictedError
)
from backend.services.video_merger import merge_video_audio_streams, remux_video_container
from backend.services.audio_converter import process_audio_conversion
from backend.services.torrent_service import is_torrent_url, run_torrent_download, extract_torrent_or_magnet_url
from backend.config import settings

logger = logging.getLogger("mediaflow.job_manager")

class JobManager:
    def __init__(self):
        self._jobs: Dict[str, JobProgress] = {}
        self._history: List[JobHistoryItem] = []
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_JOBS)
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}

    async def create_job(
        self,
        media_title: Optional[str] = None,
        thumbnail: Optional[str] = None,
        selected_format: Optional[str] = None
    ) -> str:
        job_id = str(uuid.uuid4())
        progress = JobProgress(
            job_id=job_id,
            status=JobStatus.QUEUED,
            phase="Job initialized in queue...",
            percent=0.0,
            media_title=media_title or "Media Download",
            media_thumbnail=thumbnail,
            selected_format=selected_format,
            created_at=time.time(),
            updated_at=time.time()
        )
        async with self._lock:
            self._jobs[job_id] = progress
            self._subscribers[job_id] = []
        return job_id

    async def get_job(self, job_id: str) -> Optional[JobProgress]:
        async with self._lock:
            return self._jobs.get(job_id)

    async def get_history(self) -> List[JobHistoryItem]:
        async with self._lock:
            return list(self._history)

    async def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        phase: Optional[str] = None,
        percent: Optional[float] = None,
        speed_str: Optional[str] = None,
        eta_str: Optional[str] = None,
        downloaded_bytes: Optional[int] = None,
        total_bytes: Optional[int] = None,
        file_name: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        output_path: Optional[str] = None,
        error: Optional[str] = None
    ):
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return

            if status is not None:
                job.status = status
            if phase is not None:
                job.phase = phase
            if percent is not None:
                job.percent = max(0.0, min(100.0, round(percent, 1)))
            if speed_str is not None:
                job.speed_str = speed_str
            if eta_str is not None:
                job.eta_str = eta_str
            if downloaded_bytes is not None:
                job.downloaded_bytes = downloaded_bytes
            if total_bytes is not None:
                job.total_bytes = total_bytes
            if file_name is not None:
                job.file_name = file_name
            if file_size_bytes is not None:
                job.file_size_bytes = file_size_bytes
            if output_path is not None:
                job.output_path = output_path
                job.download_url = f"/api/jobs/{job_id}/download"
            if error is not None:
                job.error = error

            job.updated_at = time.time()

            # If completed, add to history
            if job.status == JobStatus.COMPLETED and job.file_name:
                history_item = JobHistoryItem(
                    job_id=job.job_id,
                    title=job.media_title or job.file_name,
                    thumbnail=job.media_thumbnail,
                    format_type=job.selected_format or "Media",
                    selected_quality=job.phase or "Completed",
                    file_size_bytes=job.file_size_bytes,
                    completed_at=time.time(),
                    file_name=job.file_name
                )
                # Keep last 50 history items
                self._history.insert(0, history_item)
                if len(self._history) > 50:
                    self._history.pop()

            # Broadcast to SSE queues
            queues = self._subscribers.get(job_id, [])
            for q in queues:
                await q.put(job.model_dump())

    async def subscribe(self, job_id: str) -> AsyncGenerator[Dict, None]:
        q = asyncio.Queue()
        async with self._lock:
            if job_id not in self._jobs:
                return
            if job_id not in self._subscribers:
                self._subscribers[job_id] = []
            self._subscribers[job_id].append(q)
            # Send current state immediately
            await q.put(self._jobs[job_id].model_dump())

        try:
            while True:
                data = await q.get()
                yield data
                if data.get("status") in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
                    break
        finally:
            async with self._lock:
                if job_id in self._subscribers and q in self._subscribers[job_id]:
                    self._subscribers[job_id].remove(q)

    def _create_ytdlp_progress_hook(self, job_id: str, loop: asyncio.AbstractEventLoop, stream_name: str = "media"):
        def hook(d):
            if d.get("status") == "downloading":
                total_raw = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded_raw = d.get("downloaded_bytes") or 0
                try:
                    total = int(float(total_raw)) if total_raw else 0
                except (ValueError, TypeError):
                    total = 0
                try:
                    downloaded = int(float(downloaded_raw)) if downloaded_raw else 0
                except (ValueError, TypeError):
                    downloaded = 0
                speed = d.get("speed")
                eta = d.get("eta")

                pct = 0.0
                if total > 0:
                    pct = (downloaded / total) * 80.0  # Reserve last 20% for ffmpeg processing
                elif downloaded > 0:
                    pct = min(75.0, (downloaded / (50 * 1024 * 1024)) * 50.0)

                speed_str = f"{float(speed) / (1024*1024):.1f} MB/s" if speed is not None else None
                eta_str = None
                if eta is not None:
                    try:
                        eta_sec = int(float(eta))
                        eta_str = f"{eta_sec // 60:02d}:{eta_sec % 60:02d}"
                    except (ValueError, TypeError):
                        eta_str = None

                phase_msg = f"Downloading {stream_name}... {pct:.0f}%"
                if speed_str:
                    phase_msg += f" ({speed_str})"

                try:
                    if not loop.is_closed():
                        asyncio.run_coroutine_threadsafe(
                            self.update_job(
                                job_id,
                                status=JobStatus.DOWNLOADING,
                                phase=phase_msg,
                                percent=pct,
                                speed_str=speed_str,
                                eta_str=eta_str,
                                downloaded_bytes=downloaded,
                                total_bytes=total if total > 0 else None
                            ),
                            loop
                        )
                except Exception as ex:
                    logger.debug(f"Failed to post download progress update: {ex}")
        return hook

    async def run_torrent_job(self, job_id: str, req: VideoDownloadRequest):
        job_dir = get_job_temp_dir(job_id)
        try:
            await self.update_job(
                job_id,
                status=JobStatus.PREPARING,
                phase="Initializing BitTorrent engine & peer discovery...",
                percent=3.0
            )

            async def progress_callback(status: str, phase: str, percent: float, speed: str, eta: str):
                await self.update_job(
                    job_id,
                    status=JobStatus[status],
                    phase=phase,
                    percent=percent,
                    speed_str=speed,
                    eta_str=eta
                )

            clean_torrent_url = extract_torrent_or_magnet_url(req.url) or req.url.strip()
            final_path, final_name, file_size = await run_torrent_download(
                job_id, clean_torrent_url, job_dir, progress_callback
            )

            await self.update_job(
                job_id,
                status=JobStatus.COMPLETED,
                phase="Completed",
                percent=100.0,
                file_name=final_name,
                file_size_bytes=file_size,
                output_path=final_path
            )
            logger.info(f"Torrent job {job_id} completed successfully: {final_name} ({file_size} bytes)")

        except Exception as e:
            logger.error(f"Torrent job {job_id} failed: {e}")
            cleanup_job_dir(job_id)
            await self.update_job(
                job_id,
                status=JobStatus.FAILED,
                error=f"Torrent download failed: {str(e)}",
                phase="Download Failed"
            )

    async def run_video_job(self, job_id: str, req: VideoDownloadRequest):
        loop = asyncio.get_running_loop()
        async with self._semaphore:
            # Check if this is a BitTorrent download
            if is_torrent_url(req.url):
                await self.run_torrent_job(job_id, req)
                return

            job_dir = get_job_temp_dir(job_id)
            try:
                await self.update_job(job_id, status=JobStatus.PREPARING, phase="Preparing media streams...", percent=5.0)

                # Fetch info
                info = await asyncio.to_thread(analyze_media_url, req.url)
                title = req.title or info.get("title") or "Video"
                clean_title = sanitize_filename(title, fallback="video")
                duration = info.get("duration")

                container = req.container.lower() if req.container in ["mp4", "webm", "mkv"] else "mp4"
                final_filename = f"{clean_title}.{container}"
                final_output_path = str(job_dir / final_filename)

                hook = self._create_ytdlp_progress_hook(job_id, loop, "video stream")

                # If audio format ID specified and separate, we download video & audio then merge
                if req.audio_format_id and req.audio_format_id != "none":
                    video_tmp_path = str(job_dir / "temp_video.%(ext)s")
                    audio_tmp_path = str(job_dir / "temp_audio.%(ext)s")

                    # Download video stream
                    await self.update_job(job_id, status=JobStatus.DOWNLOADING, phase="Downloading video stream...", percent=10.0)
                    v_info = await asyncio.to_thread(download_media_stream, req.url, req.format_id, video_tmp_path, hook)
                    
                    # Find downloaded video file
                    downloaded_v_file = None
                    for f in job_dir.iterdir():
                        if f.name.startswith("temp_video.") and not f.name.endswith(".part") and not f.name.endswith(".ytdl"):
                            downloaded_v_file = str(f)
                            break
                    if not downloaded_v_file:
                        raise ExtractorError("Failed to capture downloaded video stream.")

                    # Download audio stream
                    audio_hook = self._create_ytdlp_progress_hook(job_id, loop, "audio stream")
                    await self.update_job(job_id, status=JobStatus.DOWNLOADING, phase="Downloading audio stream...", percent=75.0)
                    a_info = await asyncio.to_thread(download_media_stream, req.url, req.audio_format_id, audio_tmp_path, audio_hook)

                    downloaded_a_file = None
                    for f in job_dir.iterdir():
                        if f.name.startswith("temp_audio.") and not f.name.endswith(".part") and not f.name.endswith(".ytdl"):
                            downloaded_a_file = str(f)
                            break
                    if not downloaded_a_file:
                        raise ExtractorError("Failed to capture downloaded audio stream.")

                    # Merge using FFmpeg
                    await self.update_job(job_id, status=JobStatus.PROCESSING, phase="Merging video + audio...", percent=85.0)
                    
                    def ffmpeg_callback(pct, msg):
                        merged_pct = 85.0 + (pct * 0.14)
                        try:
                            if not loop.is_closed():
                                asyncio.run_coroutine_threadsafe(
                                    self.update_job(job_id, status=JobStatus.PROCESSING, phase=f"Merging streams ({pct:.0f}%)...", percent=merged_pct),
                                    loop
                                )
                        except Exception as ex:
                            logger.debug(f"Failed to post ffmpeg progress update: {ex}")

                    success = await asyncio.to_thread(
                        merge_video_audio_streams,
                        downloaded_v_file, downloaded_a_file, final_output_path, container, duration, ffmpeg_callback
                    )

                    # Clean up temp stream fragments
                    for f in [downloaded_v_file, downloaded_a_file]:
                        if f and os.path.exists(f):
                            try:
                                os.remove(f)
                            except Exception:
                                pass

                    if not success or not os.path.exists(final_output_path):
                        raise ExtractorError("Failed to merge video and audio streams.")

                else:
                    # Single combined stream download
                    single_tmp = str(job_dir / "temp_media.%(ext)s")
                    single_hook = self._create_ytdlp_progress_hook(job_id, loop, "media")
                    await self.update_job(job_id, status=JobStatus.DOWNLOADING, phase="Downloading media...", percent=10.0)
                    await asyncio.to_thread(download_media_stream, req.url, req.format_id, single_tmp, single_hook)
                    
                    downloaded_file = None
                    for f in job_dir.iterdir():
                        if f.name.startswith("temp_media.") and not f.name.endswith(".part") and not f.name.endswith(".ytdl"):
                            downloaded_file = str(f)
                            break
                            
                    if not downloaded_file:
                        raise ExtractorError("Downloaded media file not found.")

                    # If container matches, rename directly; otherwise remux
                    src_ext = downloaded_file.split(".")[-1].lower()
                    if src_ext == container:
                        shutil.move(downloaded_file, final_output_path)
                    else:
                        await self.update_job(job_id, status=JobStatus.PROCESSING, phase=f"Remuxing to {container.upper()}...", percent=88.0)
                        
                        def remux_callback(pct, msg):
                            remux_pct = 88.0 + (pct * 0.11)
                            try:
                                if not loop.is_closed():
                                    asyncio.run_coroutine_threadsafe(
                                        self.update_job(job_id, status=JobStatus.PROCESSING, phase=f"Remuxing to {container.upper()} ({pct:.0f}%)...", percent=remux_pct),
                                        loop
                                    )
                            except Exception as ex:
                                logger.debug(f"Failed to post remux progress update: {ex}")

                        remux_success = await asyncio.to_thread(
                            remux_video_container, downloaded_file, final_output_path, container, duration, remux_callback
                        )
                        if os.path.exists(downloaded_file):
                            try:
                                os.remove(downloaded_file)
                            except Exception:
                                pass
                        if not remux_success:
                            raise ExtractorError(f"Failed to remux to {container.upper()}.")

                final_size = get_file_size(final_output_path)
                await self.update_job(
                    job_id,
                    status=JobStatus.COMPLETED,
                    phase="Completed",
                    percent=100.0,
                    file_name=final_filename,
                    file_size_bytes=final_size,
                    output_path=final_output_path
                )
                logger.info(f"Video job {job_id} completed successfully: {final_filename}")

            except MediaRestrictedError as e:
                logger.warning(f"Job {job_id} restricted: {e}")
                cleanup_job_dir(job_id)
                await self.update_job(job_id, status=JobStatus.FAILED, error=str(e), phase="Protected / Restricted Media")
            except ExtractorError as e:
                logger.error(f"Job {job_id} extraction error: {e}")
                cleanup_job_dir(job_id)
                await self.update_job(job_id, status=JobStatus.FAILED, error=str(e), phase="Download Failed")
            except Exception as e:
                logger.error(f"Job {job_id} unexpected error: {e}")
                cleanup_job_dir(job_id)
                await self.update_job(job_id, status=JobStatus.FAILED, error=f"Processing failed: {str(e)}", phase="Error")

    async def run_audio_job(self, job_id: str, req: AudioDownloadRequest):
        loop = asyncio.get_running_loop()
        async with self._semaphore:
            job_dir = get_job_temp_dir(job_id)
            try:
                await self.update_job(job_id, status=JobStatus.PREPARING, phase="Preparing audio stream...", percent=5.0)

                # Fetch metadata
                info = await asyncio.to_thread(analyze_media_url, req.url)
                title = req.title or info.get("title") or "Audio"
                clean_title = sanitize_filename(title, fallback="audio")
                duration = info.get("duration")

                format_lower = req.format.lower()
                
                # Determine final file extension
                ext_map = {
                    "mp3": "mp3", "flac": "flac", "wav": "wav", "m4a": "m4a",
                    "aac": "aac", "ogg": "ogg", "opus": "opus", "alac": "m4a",
                    "aiff": "aiff", "original": "m4a"
                }
                final_ext = ext_map.get(format_lower, "mp3")
                final_filename = f"{clean_title}.{final_ext}"
                final_output_path = str(job_dir / final_filename)

                # Pick format to download: prefer specified audio_format_id or 'bestaudio/best'
                fmt_selector = req.audio_format_id if req.audio_format_id else "bestaudio/best"
                temp_source_path = str(job_dir / "source_audio.%(ext)s")

                hook = self._create_ytdlp_progress_hook(job_id, loop, "audio source")
                await self.update_job(job_id, status=JobStatus.DOWNLOADING, phase="Downloading audio source...", percent=10.0)
                await asyncio.to_thread(download_media_stream, req.url, fmt_selector, temp_source_path, hook)

                downloaded_file = None
                for f in job_dir.iterdir():
                    if f.name.startswith("source_audio.") and not f.name.endswith(".part") and not f.name.endswith(".ytdl"):
                        downloaded_file = str(f)
                        break
                        
                if not downloaded_file:
                    raise ExtractorError("Source audio stream could not be downloaded.")

                # If user selected original and downloaded extension matches, copy directly
                source_ext = downloaded_file.split(".")[-1].lower()
                if format_lower == "original":
                    final_filename = f"{clean_title}.{source_ext}"
                    final_output_path = str(job_dir / final_filename)

                phase_label = f"Converting to {format_lower.upper()}..." if format_lower != "original" else "Extracting original audio..."
                await self.update_job(job_id, status=JobStatus.PROCESSING, phase=phase_label, percent=82.0)

                def audio_ffmpeg_callback(pct, msg):
                    overall = 82.0 + (pct * 0.17)
                    try:
                        if not loop.is_closed():
                            asyncio.run_coroutine_threadsafe(
                                self.update_job(job_id, status=JobStatus.PROCESSING, phase=f"{phase_label} ({pct:.0f}%)", percent=overall),
                                loop
                            )
                    except Exception as ex:
                        logger.debug(f"Failed to post audio ffmpeg progress update: {ex}")

                success = await asyncio.to_thread(
                    process_audio_conversion,
                    downloaded_file, final_output_path, req, duration, audio_ffmpeg_callback
                )

                # Clean temporary source file
                if downloaded_file and os.path.exists(downloaded_file) and downloaded_file != final_output_path:
                    try:
                        os.remove(downloaded_file)
                    except Exception:
                        pass

                if not success or not os.path.exists(final_output_path):
                    raise ExtractorError(f"Audio conversion to {format_lower.upper()} failed.")

                final_size = get_file_size(final_output_path)
                await self.update_job(
                    job_id,
                    status=JobStatus.COMPLETED,
                    phase="Completed",
                    percent=100.0,
                    file_name=final_filename,
                    file_size_bytes=final_size,
                    output_path=final_output_path
                )
                logger.info(f"Audio job {job_id} completed successfully: {final_filename}")

            except MediaRestrictedError as e:
                logger.warning(f"Audio job {job_id} restricted: {e}")
                cleanup_job_dir(job_id)
                await self.update_job(job_id, status=JobStatus.FAILED, error=str(e), phase="Protected / Restricted Media")
            except ExtractorError as e:
                logger.error(f"Audio job {job_id} extraction error: {e}")
                cleanup_job_dir(job_id)
                await self.update_job(job_id, status=JobStatus.FAILED, error=str(e), phase="Download Failed")
            except Exception as e:
                logger.error(f"Audio job {job_id} unexpected error: {e}")
                cleanup_job_dir(job_id)
                await self.update_job(job_id, status=JobStatus.FAILED, error=f"Conversion failed: {str(e)}", phase="Error")

job_manager = JobManager()
