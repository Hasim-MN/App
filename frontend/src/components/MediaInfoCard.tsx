'use client';

import React from 'react';
import { Play, Clock, User, Eye, Calendar, Music, Sparkles, Film } from 'lucide-react';
import { MediaInfo } from '@/lib/types';
import { formatNumber } from '@/lib/utils';

interface MediaInfoCardProps {
  media: MediaInfo;
}

export default function MediaInfoCard({ media }: MediaInfoCardProps) {
  const audio = media.original_audio;

  return (
    <div className="w-full max-w-5xl mx-auto px-4 mb-6">
      <div className="glass-panel rounded-2xl p-4 sm:p-6 border border-slate-800/80 shadow-2xl relative overflow-hidden">
        
        {/* Subtle background glow */}
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="flex flex-col md:flex-row gap-5 sm:gap-6 items-start">
          
          {/* Thumbnail Preview with Duration Badge */}
          <div className="relative w-full md:w-72 sm:h-44 h-48 rounded-xl overflow-hidden bg-slate-950 border border-slate-800 shrink-0 group">
            {media.thumbnail ? (
              <img
                src={media.thumbnail}
                alt={media.title}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              />
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center text-slate-600 bg-slate-900">
                <Film className="w-10 h-10 mb-1 opacity-50" />
                <span className="text-xs">Media Preview</span>
              </div>
            )}

            {/* Duration Badge */}
            {media.duration_formatted && (
              <div className="absolute bottom-2.5 right-2.5 px-2 py-0.5 rounded-md bg-black/80 backdrop-blur-md border border-white/10 text-white text-xs font-mono font-medium flex items-center gap-1 shadow-lg">
                <Clock className="w-3 h-3 text-cyan-400" />
                <span>{media.duration_formatted}</span>
              </div>
            )}

            {/* Source Tag */}
            <div className="absolute top-2.5 left-2.5 px-2 py-0.5 rounded-md bg-slate-900/90 backdrop-blur-md border border-slate-700/80 text-cyan-300 text-[11px] font-semibold tracking-wide uppercase">
              {media.source}
            </div>
          </div>

          {/* Media Info Meta */}
          <div className="flex-1 min-w-0 space-y-3">
            
            {/* Title */}
            <div>
              <h2 className="text-lg sm:text-xl font-bold text-white leading-snug break-words">
                {media.title}
              </h2>
              
              {/* Channel / Views / Date Meta Row */}
              <div className="flex flex-wrap items-center gap-y-1 gap-x-4 mt-2 text-xs text-slate-400">
                {media.uploader && (
                  <div className="flex items-center gap-1.5 text-slate-300 font-medium">
                    <User className="w-3.5 h-3.5 text-indigo-400" />
                    <span>{media.uploader}</span>
                  </div>
                )}
                {media.view_count !== undefined && media.view_count !== null && (
                  <div className="flex items-center gap-1.5">
                    <Eye className="w-3.5 h-3.5 text-slate-500" />
                    <span>{formatNumber(media.view_count)} views</span>
                  </div>
                )}
                {media.upload_date && (
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-slate-500" />
                    <span>{media.upload_date}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Description Preview */}
            {media.description && (
              <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                {media.description}
              </p>
            )}

            {/* Original Audio Source Inspector Badge */}
            {audio && (
              <div className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="p-1 rounded-lg bg-cyan-500/10 text-cyan-400">
                    <Music className="w-3.5 h-3.5" />
                  </div>
                  <div className="text-xs">
                    <span className="font-semibold text-slate-200">Source Audio Stream: </span>
                    <span className="text-cyan-300 font-mono">
                      {audio.codec} • {audio.bitrate_kbps ? `${Math.round(audio.bitrate_kbps)} kbps` : 'Standard'} • {audio.sample_rate_hz ? `${audio.sample_rate_hz / 1000} kHz` : '48 kHz'} • {audio.channel_layout || 'Stereo'}
                    </span>
                  </div>
                </div>

                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800/80 font-medium">
                  Direct extraction ready
                </span>
              </div>
            )}

          </div>

        </div>

      </div>
    </div>
  );
}
