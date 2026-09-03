'use client';

import React, { useState } from 'react';
import { Download, ChevronDown, ChevronUp, Layers, Video, Volume2, ShieldCheck, Sparkles } from 'lucide-react';
import { VideoFormat } from '@/lib/types';
import { formatBytes } from '@/lib/utils';

interface VideoOptionsTableProps {
  formats: VideoFormat[];
  onDownloadVideo: (format: VideoFormat, container: string) => void;
  isDownloading: boolean;
}

export default function VideoOptionsTable({
  formats,
  onDownloadVideo,
  isDownloading,
}: VideoOptionsTableProps) {
  const [selectedContainer, setSelectedContainer] = useState<string>('mp4');
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  if (!formats || formats.length === 0) {
    return (
      <div className="w-full max-w-5xl mx-auto px-4 py-8 text-center text-slate-400 glass-panel rounded-2xl">
        <Video className="w-8 h-8 mx-auto text-slate-600 mb-2" />
        <p className="text-sm">No downloadable video streams were discovered for this URL.</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-5xl mx-auto px-4 space-y-4">
      
      {/* Container Selector & Table Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 glass-panel rounded-2xl border border-slate-800">
        
        {/* Container Picker */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Target Container:
          </span>
          <div className="inline-flex p-1 rounded-xl bg-slate-950 border border-slate-800">
            {['mp4', 'webm', 'mkv'].map((container) => (
              <button
                key={container}
                id={`btn-container-${container}`}
                onClick={() => setSelectedContainer(container)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold uppercase transition-all cursor-pointer ${
                  selectedContainer === container
                    ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {container}
              </button>
            ))}
          </div>
        </div>

        {/* Stream Copy Indicator */}
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span>Smart FFmpeg stream copy with zero generation loss</span>
        </div>

      </div>

      {/* Desktop Table View */}
      <div className="hidden md:block glass-panel rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/80 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3.5 px-4">Quality</th>
                <th className="py-3.5 px-4">Resolution</th>
                <th className="py-3.5 px-4">FPS</th>
                <th className="py-3.5 px-4">Container</th>
                <th className="py-3.5 px-4">Video Codec</th>
                <th className="py-3.5 px-4">Audio Stream</th>
                <th className="py-3.5 px-4">Est. Size</th>
                <th className="py-3.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium text-slate-300">
              {formats.map((fmt, index) => {
                const isHighRes = (fmt.height || 0) >= 1080;
                return (
                  <tr
                    key={fmt.format_id || index}
                    className="hover:bg-slate-800/40 transition-colors group"
                  >
                    {/* Quality Badge */}
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-md font-bold text-[11px] ${
                        isHighRes
                          ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/80'
                          : 'bg-slate-800 text-slate-300'
                      }`}>
                        {fmt.quality_label}
                      </span>
                    </td>

                    {/* Resolution */}
                    <td className="py-3.5 px-4 font-mono text-slate-200">
                      {fmt.resolution}
                    </td>

                    {/* FPS */}
                    <td className="py-3.5 px-4 font-mono">
                      {fmt.fps ? `${fmt.fps} FPS` : '30 FPS'}
                    </td>

                    {/* Container */}
                    <td className="py-3.5 px-4 font-mono uppercase text-cyan-400">
                      {selectedContainer}
                    </td>

                    {/* Video Codec */}
                    <td className="py-3.5 px-4">
                      <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 font-mono text-[11px] text-slate-300">
                        {fmt.video_codec || 'H.264'}
                      </span>
                    </td>

                    {/* Audio Stream Info */}
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-1.5 text-slate-400">
                        <Volume2 className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                        <span className="text-[11px]">
                          {fmt.has_audio ? 'Embedded' : 'Auto-merged (Best)'}
                        </span>
                      </div>
                    </td>

                    {/* Estimated Size */}
                    <td className="py-3.5 px-4 font-mono text-slate-200">
                      {fmt.estimated_size_bytes ? formatBytes(fmt.estimated_size_bytes) : 'Calculating...'}
                    </td>

                    {/* Download Button */}
                    <td className="py-3.5 px-4 text-right">
                      <button
                        id={`btn-download-video-${fmt.format_id}`}
                        onClick={() => onDownloadVideo(fmt, selectedContainer)}
                        disabled={isDownloading}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white text-xs font-semibold shadow-md shadow-cyan-500/20 transition-all disabled:opacity-50 cursor-pointer"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mobile Stacked Format Cards */}
      <div className="grid grid-cols-1 gap-3 md:hidden">
        {formats.map((fmt, index) => (
          <div
            key={fmt.format_id || index}
            className="p-4 glass-panel rounded-2xl border border-slate-800 space-y-3"
          >
            <div className="flex items-center justify-between">
              <span className="px-2.5 py-1 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-800/80 font-bold text-xs">
                {fmt.quality_label}
              </span>
              <span className="text-xs font-mono font-bold text-white">
                {fmt.estimated_size_bytes ? formatBytes(fmt.estimated_size_bytes) : 'Dynamic size'}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs text-slate-400 pt-1">
              <div>
                <span className="text-slate-500">Resolution:</span> {fmt.resolution}
              </div>
              <div>
                <span className="text-slate-500">FPS:</span> {fmt.fps ? `${fmt.fps} FPS` : '30 FPS'}
              </div>
              <div>
                <span className="text-slate-500">Codec:</span> {fmt.video_codec || 'H.264'}
              </div>
              <div>
                <span className="text-slate-500">Container:</span> <span className="uppercase text-cyan-400 font-mono">{selectedContainer}</span>
              </div>
            </div>

            <button
              onClick={() => onDownloadVideo(fmt, selectedContainer)}
              disabled={isDownloading}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 text-white text-xs font-semibold shadow-md transition-all cursor-pointer"
            >
              <Download className="w-4 h-4" />
              <span>Download ({selectedContainer.toUpperCase()})</span>
            </button>
          </div>
        ))}
      </div>

      {/* Advanced Video Options Collapsible */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="w-full flex items-center justify-between p-4 text-xs font-semibold text-slate-300 hover:text-white transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>Advanced Video & Codec Options</span>
          </div>
          {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showAdvanced && (
          <div className="p-4 pt-0 border-t border-slate-800/60 text-xs text-slate-400 space-y-3 animate-in fade-in duration-200">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="font-semibold text-slate-200 block mb-1">H.264 / AVC</span>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Maximum compatibility across all browsers, smart TVs, Apple, and Android devices.
                </p>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="font-semibold text-slate-200 block mb-1">VP9 / AV1</span>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  High-efficiency next-gen codecs for 2K/4K/8K resolutions with smaller file footprints.
                </p>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="font-semibold text-slate-200 block mb-1">Audio Stream Merging</span>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Separate high-res video and AAC/Opus streams are merged seamlessly with zero re-encoding loss.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
