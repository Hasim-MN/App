'use client';

import React from 'react';
import { Film, Music2, Sparkles } from 'lucide-react';

export type ActiveTab = 'video' | 'audio';

interface FormatTabsProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  videoCount: number;
  audioCount: number;
}

export default function FormatTabs({
  activeTab,
  setActiveTab,
  videoCount,
  audioCount,
}: FormatTabsProps) {
  return (
    <div className="w-full max-w-5xl mx-auto px-4 mb-6">
      <div className="flex p-1.5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl max-w-md mx-auto">
        
        {/* Video Tab */}
        <button
          id="tab-video"
          onClick={() => setActiveTab('video')}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
            activeTab === 'video'
              ? 'bg-gradient-to-r from-cyan-500 to-indigo-600 text-white shadow-lg shadow-cyan-500/25'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
          }`}
        >
          <Film className="w-4 h-4" />
          <span>Video Stream</span>
          <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
            activeTab === 'video' ? 'bg-white/20 text-white' : 'bg-slate-800 text-slate-400'
          }`}>
            {videoCount}
          </span>
        </button>

        {/* Audio Converter Tab */}
        <button
          id="tab-audio"
          onClick={() => setActiveTab('audio')}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
            activeTab === 'audio'
              ? 'bg-gradient-to-r from-cyan-500 to-indigo-600 text-white shadow-lg shadow-cyan-500/25'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
          }`}
        >
          <Music2 className="w-4 h-4" />
          <span>Audio Converter</span>
          <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
            activeTab === 'audio' ? 'bg-white/20 text-white' : 'bg-slate-800 text-slate-400'
          }`}>
            {audioCount}
          </span>
        </button>

      </div>
    </div>
  );
}
