'use client';

import React, { useEffect } from 'react';
import { 
  X, Download, CheckCircle2, AlertCircle, Loader2, 
  HardDrive, Zap, Clock, ShieldAlert, Sparkles, RefreshCw 
} from 'lucide-react';
import { JobProgress } from '@/lib/types';
import { getDownloadUrl } from '@/lib/api';
import { formatBytes, triggerConfetti } from '@/lib/utils';

interface DownloadProgressModalProps {
  progress: JobProgress | null;
  isOpen: boolean;
  onClose: () => void;
  onRetry?: () => void;
}

export default function DownloadProgressModal({
  progress,
  isOpen,
  onClose,
  onRetry,
}: DownloadProgressModalProps) {
  const isCompleted = progress?.status === 'COMPLETED';
  const isFailed = progress?.status === 'FAILED';
  const isDownloading = progress?.status === 'DOWNLOADING';
  const isProcessing = progress?.status === 'PROCESSING';

  // Trigger celebration confetti on complete
  useEffect(() => {
    if (isCompleted) {
      triggerConfetti();
    }
  }, [isCompleted]);

  if (!isOpen || !progress) return null;

  const downloadUrl = getDownloadUrl(progress.job_id);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg glass-panel rounded-3xl p-6 sm:p-8 border border-slate-700 shadow-2xl space-y-6">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className={`p-2.5 rounded-2xl ${
              isCompleted 
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                : isFailed 
                ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' 
                : 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
            }`}>
              {isCompleted ? (
                <CheckCircle2 className="w-6 h-6" />
              ) : isFailed ? (
                <ShieldAlert className="w-6 h-6" />
              ) : (
                <Loader2 className="w-6 h-6 animate-spin" />
              )}
            </div>
            <div>
              <h3 className="text-base font-bold text-white">
                {isCompleted
                  ? 'Media Ready for Download'
                  : isFailed
                  ? 'Processing Notice'
                  : 'Processing Media'}
              </h3>
              <p className="text-xs text-slate-400">
                {progress.media_title || 'MediaFlow Downloader Task'}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Phase Message & Progress Percentage */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="text-slate-300 font-medium">{progress.phase}</span>
            <span className="font-mono text-cyan-400 text-sm">
              {progress.percent.toFixed(0)}%
            </span>
          </div>

          {/* Animated Progress Bar */}
          <div className="w-full h-3.5 bg-slate-950 rounded-full overflow-hidden p-0.5 border border-slate-800">
            <div
              className={`h-full rounded-full transition-all duration-300 ${
                isCompleted
                  ? 'bg-gradient-to-r from-emerald-400 to-teal-500 shadow-lg shadow-emerald-500/40'
                  : isFailed
                  ? 'bg-rose-500'
                  : 'bg-gradient-to-r from-cyan-500 via-indigo-500 to-purple-500 shadow-lg shadow-cyan-500/40'
              }`}
              style={{ width: `${Math.max(5, Math.min(100, progress.percent))}%` }}
            ></div>
          </div>
        </div>

        {/* Live Metrics Grid (Speed, ETA, Size) */}
        {!isFailed && (
          <div className="grid grid-cols-3 gap-2 p-3 rounded-2xl bg-slate-950/70 border border-slate-800 text-center">
            <div>
              <span className="text-[10px] text-slate-500 block uppercase font-mono">Speed</span>
              <span className="text-xs font-mono font-semibold text-slate-200">
                {progress.speed_str || (isCompleted ? 'Finished' : 'Calculating...')}
              </span>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 block uppercase font-mono">ETA</span>
              <span className="text-xs font-mono font-semibold text-slate-200">
                {progress.eta_str || (isCompleted ? '00:00' : '--:--')}
              </span>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 block uppercase font-mono">File Size</span>
              <span className="text-xs font-mono font-semibold text-slate-200">
                {progress.file_size_bytes 
                  ? formatBytes(progress.file_size_bytes) 
                  : (progress.downloaded_bytes ? formatBytes(progress.downloaded_bytes) : 'Calculating...')}
              </span>
            </div>
          </div>
        )}

        {/* Failure Explanation */}
        {isFailed && (
          <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-800/80 text-xs text-rose-300 space-y-2">
            <div className="flex items-center gap-2 font-semibold text-rose-200">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>Operation Could Not Be Completed</span>
            </div>
            <p className="leading-relaxed">
              {progress.error || 'The requested stream is protected by DRM or unavailable on the server.'}
            </p>
          </div>
        )}

        {/* Actions Footer */}
        <div className="pt-2">
          {isCompleted ? (
            <a
              id="btn-direct-download-file"
              href={downloadUrl}
              download={progress.file_name || 'media'}
              className="w-full flex items-center justify-center gap-2.5 py-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold text-sm shadow-xl shadow-emerald-500/25 transition-all cursor-pointer"
            >
              <Download className="w-5 h-5" />
              <span>Download File ({progress.file_name})</span>
            </a>
          ) : isFailed ? (
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="flex-1 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
              >
                Dismiss
              </button>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold transition-all"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Try Again</span>
                </button>
              )}
            </div>
          ) : (
            <div className="text-center text-xs text-slate-500 py-1 font-mono">
              Merging and conversion performed securely via FFmpeg...
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
