'use client';

import React, { useState, useEffect } from 'react';
import { Sparkles, History, Activity, ShieldCheck, Film, Music2, Server } from 'lucide-react';
import { getHealth } from '@/lib/api';
import { SystemHealth } from '@/lib/types';
import SystemHealthModal from './SystemHealthModal';
import HistoryDrawer from './HistoryDrawer';
import ServerSettingsModal from './ServerSettingsModal';

interface NavbarProps {
  onSelectHistoryUrl?: (url: string) => void;
}

export default function Navbar({ onSelectHistoryUrl }: NavbarProps) {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [isHealthOpen, setIsHealthOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isServerOpen, setIsServerOpen] = useState(false);

  const fetchHealth = () => {
    getHealth()
      .then(setHealth)
      .catch((err) => {
        console.error('Health check failed:', err);
        setHealth(null);
      });
  };

  useEffect(() => {
    fetchHealth();
    const handleUrlChanged = () => fetchHealth();
    window.addEventListener('mediaflow_backend_url_changed', handleUrlChanged);
    return () => window.removeEventListener('mediaflow_backend_url_changed', handleUrlChanged);
  }, []);

  const isHealthy = health?.status === 'ok';

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          
          {/* Logo */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 shadow-lg shadow-cyan-500/20 ring-1 ring-white/20">
              <Film className="w-5 h-5 text-white absolute transform -translate-x-1 -translate-y-1" />
              <Music2 className="w-4 h-4 text-cyan-200 absolute transform translate-x-1.5 translate-y-1.5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg tracking-tight text-white flex items-center">
                  Media<span className="text-gradient">Flow</span>
                </span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
                  v1.0
                </span>
              </div>
              <p className="text-xs text-slate-400 font-medium hidden sm:block">
                Universal Video Inspector & Audio Converter
              </p>
            </div>
          </div>

          {/* Right Action Controls */}
          <div className="flex items-center gap-3">
            
            {/* System Status Pill */}
            <button
              id="btn-health-status"
              onClick={() => setIsHealthOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 hover:border-slate-700 text-xs font-medium text-slate-300 transition-all hover:bg-slate-800/60"
              title="System engine diagnostic status"
            >
              <span className="relative flex h-2 w-2">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isHealthy ? 'bg-emerald-400' : 'bg-amber-400'}`}></span>
                <span className={`relative inline-flex rounded-full h-2 w-2 ${isHealthy ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
              </span>
              <span className="hidden sm:inline">Engine:</span>
              <span className={isHealthy ? 'text-emerald-400' : 'text-amber-400'}>
                {health?.dependencies.ffmpeg.available ? 'FFmpeg 8.0 Ready' : 'Degraded'}
              </span>
            </button>

            {/* Server Settings Button */}
            <button
              id="btn-server-settings"
              onClick={() => setIsServerOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-indigo-500/50 hover:text-indigo-400 text-xs font-medium text-slate-300 transition-all"
              title="Configure Backend API Server (Mobile/Cloud)"
            >
              <Server className="w-3.5 h-3.5" />
              <span className="hidden xs:inline">Server</span>
            </button>

            {/* History Button */}
            <button
              id="btn-history-toggle"
              onClick={() => setIsHistoryOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-cyan-500/50 hover:text-cyan-400 text-xs font-medium text-slate-300 transition-all"
            >
              <History className="w-3.5 h-3.5" />
              <span>History</span>
            </button>

            {/* Security Badge */}
            <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-900/60 text-[11px] font-medium text-emerald-400">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>SSRF Protected</span>
            </div>

          </div>

        </div>
      </header>

      {/* Server Settings Modal */}
      <ServerSettingsModal
        isOpen={isServerOpen}
        onClose={() => setIsServerOpen(false)}
        onServerUpdated={fetchHealth}
      />

      {/* Health Diagnostic Modal */}
      {isHealthOpen && (
        <SystemHealthModal health={health} onClose={() => setIsHealthOpen(false)} />
      )}

      {/* History Drawer */}
      <HistoryDrawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        onSelectUrl={onSelectHistoryUrl}
      />
    </>
  );
}
