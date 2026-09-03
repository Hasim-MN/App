'use client';

import React from 'react';
import { X, CheckCircle2, AlertTriangle, Cpu, HardDrive, Shield, Server } from 'lucide-react';
import { SystemHealth } from '@/lib/types';

interface SystemHealthModalProps {
  health: SystemHealth | null;
  onClose: () => void;
}

export default function SystemHealthModal({ health, onClose }: SystemHealthModalProps) {
  const isHealthy = health?.status === 'ok';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="relative w-full max-w-lg glass-panel rounded-2xl p-6 border border-slate-700/80 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">System Architecture & Health</h3>
              <p className="text-xs text-slate-400">Backend media processing engine diagnostics</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="mt-5 space-y-4">
          
          {/* Status Alert */}
          <div className={`p-3.5 rounded-xl border flex items-center gap-3 ${
            isHealthy 
              ? 'bg-emerald-950/30 border-emerald-800/60 text-emerald-300' 
              : 'bg-amber-950/30 border-amber-800/60 text-amber-300'
          }`}>
            {isHealthy ? <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" /> : <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />}
            <div className="text-xs">
              <span className="font-semibold">{isHealthy ? 'All Media Engines Active' : 'System Degraded'}</span>
              <p className="text-slate-400 mt-0.5">
                {isHealthy 
                  ? 'FFmpeg, FFprobe, and stream extractors are running at optimal performance.' 
                  : 'One or more media sub-services require administrator attention.'}
              </p>
            </div>
          </div>

          {/* Engine Dependencies Grid */}
          <div className="space-y-2.5">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Core Dependencies</h4>
            
            {/* FFmpeg */}
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-start justify-between">
              <div className="flex items-start gap-3">
                <Cpu className="w-4 h-4 text-cyan-400 mt-0.5" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-white">FFmpeg Audio/Video Merger</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">Installed</span>
                  </div>
                  <p className="text-[11px] text-slate-400 font-mono mt-0.5 break-all">
                    {health?.dependencies.ffmpeg.version || 'FFmpeg 8.0.1 (static build)'}
                  </p>
                </div>
              </div>
            </div>

            {/* FFprobe */}
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-start justify-between">
              <div className="flex items-start gap-3">
                <HardDrive className="w-4 h-4 text-indigo-400 mt-0.5" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-white">FFprobe Metadata Inspector</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">Active</span>
                  </div>
                  <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                    {health?.dependencies.ffprobe.version || 'FFprobe 8.0.1'}
                  </p>
                </div>
              </div>
            </div>

            {/* yt-dlp */}
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-start justify-between">
              <div className="flex items-start gap-3">
                <Shield className="w-4 h-4 text-purple-400 mt-0.5" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-white">yt-dlp Stream Extractor</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">Operational</span>
                  </div>
                  <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                    Version: {health?.dependencies.yt_dlp.version || 'Latest'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Security & Resource Policies */}
          <div className="p-3.5 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-1.5">
            <h4 className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">Security & Environment Policies</h4>
            <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside">
              <li>SSRF Protection: Loopback, private subnets (10.0.0.0/8, 192.168.0.0/16, etc.), and cloud metadata blocked.</li>
              <li>Safe Subprocess: Zero shell concatenation; strictly list-based commands.</li>
              <li>Auto Temp Cleanup: Isolated job sandboxes purged after 30 minutes.</li>
              <li>Max Concurrent Jobs: {health?.limits.max_concurrent_jobs || 10} concurrent tasks.</li>
            </ul>
          </div>

        </div>

        {/* Footer */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
          >
            Close Diagnostics
          </button>
        </div>

      </div>
    </div>
  );
}
