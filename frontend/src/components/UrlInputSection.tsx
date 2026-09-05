'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Search, Clipboard, X, Loader2, Sparkles, AlertCircle, ArrowRight, Video } from 'lucide-react';

interface UrlInputSectionProps {
  url: string;
  setUrl: (url: string) => void;
  onAnalyze: (targetUrl?: string) => void;
  isLoading: boolean;
  error?: string | null;
}

const SAMPLE_URLS = [
  {
    label: '🎬 Big Buck Bunny (Open Blender Movie)',
    url: 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
  },
  {
    label: '🎵 Open-License Audio Sample',
    url: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
  },
  {
    label: '🎥 Blender Foundation (YouTube Demo)',
    url: 'https://www.youtube.com/watch?v=aqz-KE-bpKQ',
  },
  {
    label: '🧲 Sintel (Open Magnet Torrent)',
    url: 'magnet:?xt=urn:btih:08ada5a7a6183aae1e09d831df6748d566095a10&dn=Sintel&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337',
  }
];

export default function UrlInputSection({
  url,
  setUrl,
  onAnalyze,
  isLoading,
  error,
}: UrlInputSectionProps) {
  const [localError, setLocalError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Validate URL format
  const validateUrl = (input: string): boolean => {
    if (!input.trim()) {
      setLocalError('Please paste or type a media URL or magnet link.');
      return false;
    }
    try {
      const parsed = new URL(input.trim());

      // Check for BitTorrent magnet link
      if (parsed.protocol === 'magnet:') {
        const xt = parsed.searchParams.get('xt');
        if (!xt || !xt.toLowerCase().startsWith('urn:btih:')) {
          setLocalError('Invalid magnet link: Missing BitTorrent infohash (urn:btih:).');
          return false;
        }
        setLocalError(null);
        return true;
      }

      if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
        setLocalError('Supported protocols: HTTP, HTTPS, and Magnet (BitTorrent).');
        return false;
      }

      // Check for incomplete YouTube links (video IDs are 11 characters)
      const host = parsed.hostname.toLowerCase();
      if (host.includes('youtu.be')) {
        const videoId = parsed.pathname.replace(/^\/+/, '').split('?')[0];
        if (videoId.length < 11) {
          setLocalError('Incomplete YouTube link. Please paste the full video URL (the 11-character video ID was cut off).');
          return false;
        }
      } else if (host.includes('youtube.com')) {
        if (parsed.pathname.includes('/watch')) {
          const v = parsed.searchParams.get('v');
          if (!v || v.length < 11) {
            setLocalError('Incomplete YouTube link. Please ensure the full 11-character video ID (?v=...) is included.');
            return false;
          }
        } else if (parsed.pathname.includes('/shorts/')) {
          const shortId = parsed.pathname.split('/shorts/')[1]?.split('?')[0];
          if (!shortId || shortId.length < 11) {
            setLocalError('Incomplete YouTube Shorts link. Please paste the full Shorts URL.');
            return false;
          }
        }
      }

      setLocalError(null);
      return true;
    } catch {
      setLocalError('Please enter a valid URL (e.g., https://...)');
      return false;
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateUrl(url)) {
      onAnalyze();
    }
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setUrl(text.trim());
        if (validateUrl(text.trim())) {
          onAnalyze(text.trim());
        }
      }
    } catch (err) {
      console.warn('Clipboard read failed:', err);
    }
  };

  const handleClear = () => {
    setUrl('');
    setLocalError(null);
    inputRef.current?.focus();
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pt-10 pb-6">
      
      {/* Hero Header */}
      <div className="text-center space-y-3 mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-cyan-400 text-xs font-semibold shadow-inner">
          <Sparkles className="w-3.5 h-3.5 animate-pulse" />
          <span>Next-Gen Media Engine with Lossless & Lossy Codecs</span>
        </div>
        
        <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight leading-tight">
          Inspect, Convert & Merge Media
        </h1>
        
        <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto">
          Analyze video streams, merge high-definition video & audio with FFmpeg stream-copy, and convert audio into 9 studio-grade formats.
        </p>
      </div>

      {/* Main URL Input Box */}
      <form onSubmit={handleSubmit} className="relative group">
        <div className="relative flex items-center rounded-2xl glass-panel-glow bg-slate-900/90 border border-slate-700/80 focus-within:border-cyan-500/80 focus-within:ring-2 focus-within:ring-cyan-500/30 transition-all p-2 sm:p-2.5 shadow-2xl">
          
          <div className="pl-3 pr-2 text-slate-500 flex items-center justify-center pointer-events-none">
            <Search className="w-5 h-5 text-cyan-400/80" />
          </div>

          <input
            id="media-url-input"
            ref={inputRef}
            type="text"
            value={url}
            onChange={(e) => {
              setUrl(e.target.value);
              if (localError) setLocalError(null);
            }}
            placeholder="Paste video, audio, or magnet torrent link... (Ctrl+V)"
            className="w-full bg-transparent text-white placeholder-slate-500 text-sm sm:text-base font-normal focus:outline-none px-2 py-2"
            disabled={isLoading}
          />

          {/* Clear Button */}
          {url && (
            <button
              type="button"
              onClick={handleClear}
              className="p-1.5 mr-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors"
              title="Clear input"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          {/* Paste Button */}
          <button
            type="button"
            id="btn-paste-url"
            onClick={handlePaste}
            className="hidden sm:flex items-center gap-1.5 px-3 py-2 mr-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-xs font-semibold text-slate-300 transition-all border border-slate-700/60"
            title="Paste from clipboard"
          >
            <Clipboard className="w-3.5 h-3.5 text-slate-400" />
            <span>Paste</span>
          </button>

          {/* Submit / Analyze Button */}
          <button
            type="submit"
            id="btn-analyze-url"
            disabled={isLoading || !url.trim()}
            className="flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white text-sm font-semibold shadow-lg shadow-cyan-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shrink-0"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Analyzing media...</span>
              </>
            ) : (
              <>
                <span>Analyze</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>

      {/* Error Message Display */}
      {(localError || error) && (
        <div className="mt-3.5 p-3 rounded-xl bg-rose-950/40 border border-rose-800/80 flex items-start gap-2.5 text-rose-300 text-xs animate-in fade-in slide-in-from-top-1 duration-200">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Analysis Notice: </span>
            <span>{localError || error}</span>
          </div>
        </div>
      )}

      {/* Quick Test Demo Links */}
      <div className="mt-5 flex flex-wrap items-center justify-center gap-2 text-xs text-slate-400">
        <span className="text-slate-500 font-medium">Try open-source demos:</span>
        {SAMPLE_URLS.map((sample, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => {
              setUrl(sample.url);
              setLocalError(null);
              onAnalyze(sample.url);
            }}
            className="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 text-slate-300 hover:text-cyan-300 transition-all font-medium text-[11px]"
          >
            {sample.label}
          </button>
        ))}
      </div>

    </div>
  );
}
