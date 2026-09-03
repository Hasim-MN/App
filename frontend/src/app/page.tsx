'use client';

import React, { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import UrlInputSection from '@/components/UrlInputSection';
import MediaInfoCard from '@/components/MediaInfoCard';
import FormatTabs, { ActiveTab } from '@/components/FormatTabs';
import VideoOptionsTable from '@/components/VideoOptionsTable';
import AudioConversionPanel from '@/components/AudioConversionPanel';
import DownloadProgressModal from '@/components/DownloadProgressModal';
import { MediaInfo, VideoFormat, JobProgress, JobHistoryItem } from '@/lib/types';
import { 
  analyzeUrl, startVideoDownload, startAudioDownload, 
  subscribeToJobProgress 
} from '@/lib/api';
import { ShieldCheck, Film, Music2, Cpu, HardDrive, CheckCircle2 } from 'lucide-react';

export default function Home() {
  const [url, setUrl] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [media, setMedia] = useState<MediaInfo | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>('video');

  // Job processing & modal state
  const [currentProgress, setCurrentProgress] = useState<JobProgress | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  const handleAnalyze = async (targetUrl?: string) => {
    const queryUrl = (targetUrl || url).trim();
    if (!queryUrl) return;

    setIsAnalyzing(true);
    setAnalyzeError(null);
    setMedia(null);

    try {
      const data = await analyzeUrl(queryUrl);
      setMedia(data);
      // Auto-switch to audio tab if no video streams were found but audio is present
      if (data.video_formats.length === 0 && data.original_audio) {
        setActiveTab('audio');
      } else {
        setActiveTab('video');
      }
    } catch (err: any) {
      setAnalyzeError(err.message || 'Failed to inspect media URL.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const saveToLocalHistory = (completedJob: JobProgress) => {
    try {
      const existing = localStorage.getItem('mediaflow_local_history');
      let items: JobHistoryItem[] = existing ? JSON.parse(existing) : [];
      const newItem: JobHistoryItem = {
        job_id: completedJob.job_id,
        title: completedJob.media_title || completedJob.file_name || 'Media',
        thumbnail: completedJob.media_thumbnail,
        format_type: completedJob.selected_format || 'Media',
        selected_quality: completedJob.phase || 'Completed',
        file_size_bytes: completedJob.file_size_bytes,
        completed_at: Date.now() / 1000,
        file_name: completedJob.file_name || 'media_file'
      };
      items.unshift(newItem);
      items = items.slice(0, 50); // Keep max 50
      localStorage.setItem('mediaflow_local_history', JSON.stringify(items));
    } catch {
      // ignore
    }
  };

  const handleDownloadVideo = async (format: VideoFormat, container: string) => {
    if (!media) return;
    setIsProcessing(true);
    setIsModalOpen(true);

    const initialProgress: JobProgress = {
      job_id: 'pending',
      status: 'QUEUED',
      phase: 'Initializing video download...',
      percent: 0,
      media_title: media.title,
      media_thumbnail: media.thumbnail,
      selected_format: `Video (${container.toUpperCase()})`,
      created_at: Date.now() / 1000,
      updated_at: Date.now() / 1000,
    };
    setCurrentProgress(initialProgress);

    try {
      const res = await startVideoDownload({
        url: media.url,
        format_id: format.format_id,
        container: container,
        audio_format_id: format.audio_format_id_for_merge,
        title: media.title,
        thumbnail: media.thumbnail,
      });

      const jobId = res.job_id;
      setCurrentProgress((prev) => prev ? { ...prev, job_id: jobId, status: 'DOWNLOADING' } : null);

      subscribeToJobProgress(
        jobId,
        (progress) => setCurrentProgress(progress),
        (completed) => {
          setCurrentProgress(completed);
          setIsProcessing(false);
          saveToLocalHistory(completed);
        },
        (error) => {
          setCurrentProgress((prev) => prev ? { ...prev, status: 'FAILED', error } : null);
          setIsProcessing(false);
        }
      );
    } catch (err: any) {
      setCurrentProgress((prev) => prev ? {
        ...prev,
        status: 'FAILED',
        error: err.message || 'Failed to start video processing job'
      } : null);
      setIsProcessing(false);
    }
  };

  const handleConvertAudio = async (params: {
    format: string;
    quality_bitrate?: string;
    ogg_quality?: number;
    sample_rate?: string;
    bit_depth?: string;
    compression_level?: number;
    channels?: string;
    normalize_audio?: boolean;
    audio_format_id?: string;
  }) => {
    if (!media) return;
    setIsProcessing(true);
    setIsModalOpen(true);

    const initialProgress: JobProgress = {
      job_id: 'pending',
      status: 'QUEUED',
      phase: 'Initializing audio conversion...',
      percent: 0,
      media_title: media.title,
      media_thumbnail: media.thumbnail,
      selected_format: `Audio (${params.format.toUpperCase()})`,
      created_at: Date.now() / 1000,
      updated_at: Date.now() / 1000,
    };
    setCurrentProgress(initialProgress);

    try {
      const res = await startAudioDownload({
        url: media.url,
        format: params.format,
        quality_bitrate: params.quality_bitrate,
        ogg_quality: params.ogg_quality,
        sample_rate: params.sample_rate,
        bit_depth: params.bit_depth,
        compression_level: params.compression_level,
        channels: params.channels,
        normalize_audio: params.normalize_audio,
        audio_format_id: params.audio_format_id || media.original_audio?.format_id,
        title: media.title,
        thumbnail: media.thumbnail,
      });

      const jobId = res.job_id;
      setCurrentProgress((prev) => prev ? { ...prev, job_id: jobId, status: 'DOWNLOADING' } : null);

      subscribeToJobProgress(
        jobId,
        (progress) => setCurrentProgress(progress),
        (completed) => {
          setCurrentProgress(completed);
          setIsProcessing(false);
          saveToLocalHistory(completed);
        },
        (error) => {
          setCurrentProgress((prev) => prev ? { ...prev, status: 'FAILED', error } : null);
          setIsProcessing(false);
        }
      );
    } catch (err: any) {
      setCurrentProgress((prev) => prev ? {
        ...prev,
        status: 'FAILED',
        error: err.message || 'Failed to start audio conversion job'
      } : null);
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen">
      
      {/* Navbar Header */}
      <Navbar onSelectHistoryUrl={(selectedUrl) => {
        setUrl(selectedUrl);
        handleAnalyze(selectedUrl);
      }} />

      {/* Main Content Area */}
      <main className="flex-1 pb-16">
        
        {/* URL Input Hero Section */}
        <UrlInputSection
          url={url}
          setUrl={setUrl}
          onAnalyze={handleAnalyze}
          isLoading={isAnalyzing}
          error={analyzeError}
        />

        {/* Media Metadata Card */}
        {media && <MediaInfoCard media={media} />}

        {/* Format Switcher & Panels */}
        {media && (
          <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
            <FormatTabs
              activeTab={activeTab}
              setActiveTab={setActiveTab}
              videoCount={media.video_formats.length}
              audioCount={media.supported_audio_formats.length}
            />

            {/* Video Formats Panel */}
            {activeTab === 'video' && (
              <VideoOptionsTable
                formats={media.video_formats}
                onDownloadVideo={handleDownloadVideo}
                isDownloading={isProcessing}
              />
            )}

            {/* Audio Converter Panel */}
            {activeTab === 'audio' && (
              <AudioConversionPanel
                media={media}
                onConvertAudio={handleConvertAudio}
                isProcessing={isProcessing}
              />
            )}
          </div>
        )}

        {/* Empty State Showcase */}
        {!media && !isAnalyzing && (
          <div className="max-w-4xl mx-auto px-4 mt-8">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              
              <div className="p-5 glass-panel rounded-2xl border border-slate-800 space-y-2">
                <div className="w-9 h-9 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20">
                  <Film className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-semibold text-white">4K & Full HD Merging</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Automatically pairs separated DASH high-definition video and audio streams with zero generation loss.
                </p>
              </div>

              <div className="p-5 glass-panel rounded-2xl border border-slate-800 space-y-2">
                <div className="w-9 h-9 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
                  <Music2 className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-semibold text-white">9 Studio Audio Formats</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Convert to MP3 (320kbps), lossless FLAC, uncompressed WAV, M4A, AAC, OPUS, OGG Vorbis, ALAC, and AIFF.
                </p>
              </div>

              <div className="p-5 glass-panel rounded-2xl border border-slate-800 space-y-2">
                <div className="w-9 h-9 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-semibold text-white">Ethical & Secure</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Built-in SSRF protections, isolated sandbox processing, safe list-based FFmpeg commands, and automatic temp purging.
                </p>
              </div>

            </div>
          </div>
        )}

      </main>

      {/* Progress & Completion Modal */}
      <DownloadProgressModal
        progress={currentProgress}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onRetry={() => {
          setIsModalOpen(false);
          if (activeTab === 'video') {
            const first = media?.video_formats[0];
            if (first) handleDownloadVideo(first, 'mp4');
          } else {
            handleConvertAudio({ format: 'mp3', quality_bitrate: '320k' });
          }
        }}
      />

      {/* Footer */}
      <footer className="w-full border-t border-slate-800/80 bg-slate-950/80 py-6 px-4 text-center text-xs text-slate-500 space-y-2">
        <p>
          MediaFlow Downloader is designed for media you own, public domain works, and authorized open licenses.
        </p>
        <p className="text-[11px] text-slate-600">
          Powered by FastAPI, FFmpeg 8.0, and Next.js. Does not bypass DRM, paywalls, or private authentication restrictions.
        </p>
      </footer>

    </div>
  );
}
