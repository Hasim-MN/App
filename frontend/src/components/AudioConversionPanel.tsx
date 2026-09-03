'use client';

import React, { useState, useMemo } from 'react';
import { 
  Music, Sparkles, AlertTriangle, Download, Sliders, Check, 
  Layers, Volume2, ShieldCheck, ArrowRight, Zap, RefreshCw 
} from 'lucide-react';
import { MediaInfo, OriginalAudioSpecs, AudioFormatOption } from '@/lib/types';
import { formatBytes } from '@/lib/utils';

interface AudioConversionPanelProps {
  media: MediaInfo;
  onConvertAudio: (params: {
    format: string;
    quality_bitrate?: string;
    ogg_quality?: number;
    sample_rate?: string;
    bit_depth?: string;
    compression_level?: number;
    channels?: string;
    normalize_audio?: boolean;
    audio_format_id?: string;
  }) => void;
  isProcessing: boolean;
}

const BITRATES_MP3 = [
  { value: '320k', label: '320 kbps — Highest MP3 Quality (Recommended)', isRec: true },
  { value: '256k', label: '256 kbps — Very High Quality' },
  { value: '192k', label: '192 kbps — High Quality' },
  { value: '160k', label: '160 kbps — CD-like Audio' },
  { value: '128k', label: '128 kbps — Standard FM Quality' },
  { value: '96k', label: '96 kbps — Compact File' },
  { value: '64k', label: '64 kbps — Voice / Low Bandwidth' },
];

const BITRATES_AAC = [
  { value: '320k', label: '320 kbps — Maximum Fidelity' },
  { value: '256k', label: '256 kbps — Apple Music Standard (Recommended)', isRec: true },
  { value: '192k', label: '192 kbps — High Quality' },
  { value: '160k', label: '160 kbps — Balanced' },
  { value: '128k', label: '128 kbps — Standard Streaming' },
  { value: '96k', label: '96 kbps — Compact' },
  { value: '64k', label: '64 kbps — Low Bandwidth' },
];

const BITRATES_OPUS = [
  { value: '256k', label: '256 kbps — Transparent High Fidelity' },
  { value: '192k', label: '192 kbps — Pro Music Quality' },
  { value: '160k', label: '160 kbps — Standard Recommended (Recommended)', isRec: true },
  { value: '128k', label: '128 kbps — Near-CD Music' },
  { value: '96k', label: '96 kbps — Clean Audio' },
  { value: '64k', label: '64 kbps — Efficient Speech & Music' },
  { value: '48k', label: '48 kbps — Ultra Compact' },
];

const OGG_VORBIS_LEVELS = [
  { value: 10, label: 'Q10 — Maximum Quality (~500 kbps)' },
  { value: 9, label: 'Q9 — Ultra High Quality (~320 kbps)' },
  { value: 8, label: 'Q8 — Very High Quality (~256 kbps)' },
  { value: 7, label: 'Q7 — High Quality (~224 kbps) (Recommended)', isRec: true },
  { value: 6, label: 'Q6 — Standard High (~192 kbps)' },
  { value: 5, label: 'Q5 — Medium High (~160 kbps)' },
  { value: 4, label: 'Q4 — Standard (~128 kbps)' },
  { value: 3, label: 'Q3 — Low Medium (~112 kbps)' },
  { value: 2, label: 'Q2 — Compact (~96 kbps)' },
  { value: 1, label: 'Q1 — Low Bandwidth (~80 kbps)' },
  { value: 0, label: 'Q0 — Minimum (~64 kbps)' },
];

const SAMPLE_RATES = [
  { value: 'original', label: 'Original (Preserve Source Rate)' },
  { value: '44100', label: '44.1 kHz (CD Audio Standard)' },
  { value: '48000', label: '48.0 kHz (Studio / Video Standard)' },
  { value: '88200', label: '88.2 kHz (High-Resolution)' },
  { value: '96000', label: '96.0 kHz (Studio Master)' },
  { value: '192000', label: '192.0 kHz (Audiophile Master)' },
];

export default function AudioConversionPanel({
  media,
  onConvertAudio,
  isProcessing,
}: AudioConversionPanelProps) {
  const audio = media.original_audio;
  const duration = media.duration_seconds || 180;

  // Selected format state
  const [selectedFormat, setSelectedFormat] = useState<string>('mp3');
  const [bitrate, setBitrate] = useState<string>('320k');
  const [oggQuality, setOggQuality] = useState<number>(7);
  const [bitDepth, setBitDepth] = useState<string>('original');
  const [sampleRate, setSampleRate] = useState<string>('original');
  const [compressionLevel, setCompressionLevel] = useState<number>(5);
  
  // Advanced settings
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [channels, setChannels] = useState<string>('original');
  const [normalizeAudio, setNormalizeAudio] = useState<boolean>(false);

  // Determine if this is an upsampling situation (source is low bitrate, converting to 320k or FLAC/WAV)
  const isUpsamplingWarning = useMemo(() => {
    if (!audio || !audio.bitrate_kbps) return false;
    const srcKbps = audio.bitrate_kbps;
    
    // If converting lossy source to FLAC/WAV/ALAC/AIFF
    if (['flac', 'wav', 'alac', 'aiff'].includes(selectedFormat)) {
      return true;
    }
    // If lossy target bitrate is significantly higher than source
    if (['mp3', 'aac', 'm4a'].includes(selectedFormat)) {
      const targetKbps = parseInt(bitrate.replace('k', ''), 10) || 320;
      if (targetKbps > srcKbps + 64) {
        return true;
      }
    }
    return false;
  }, [audio, selectedFormat, bitrate]);

  // Output file size estimation
  const estimatedOutputSize = useMemo(() => {
    if (selectedFormat === 'original' && audio?.estimated_size_bytes) {
      return audio.estimated_size_bytes;
    }

    let bytesPerSecond = 40000; // default approx ~320k

    if (['mp3', 'aac', 'm4a'].includes(selectedFormat)) {
      const kbps = parseInt(bitrate.replace('k', ''), 10) || 320;
      bytesPerSecond = (kbps * 1000) / 8;
    } else if (selectedFormat === 'opus') {
      const kbps = parseInt(bitrate.replace('k', ''), 10) || 160;
      bytesPerSecond = (kbps * 1000) / 8;
    } else if (selectedFormat === 'ogg') {
      const approxKbps = 64 + oggQuality * 44;
      bytesPerSecond = (approxKbps * 1000) / 8;
    } else if (selectedFormat === 'flac' || selectedFormat === 'alac') {
      // Lossless compression approx 50-60% of uncompressed
      const rate = sampleRate !== 'original' ? parseInt(sampleRate, 10) : 48000;
      const depth = bitDepth === '24' ? 24 : 16;
      bytesPerSecond = (rate * (depth / 8) * 2) * 0.55;
    } else if (selectedFormat === 'wav' || selectedFormat === 'aiff') {
      // Uncompressed PCM: rate * bytes_per_sample * 2 channels
      const rate = sampleRate !== 'original' ? parseInt(sampleRate, 10) : 48000;
      const depth = bitDepth === '32_float' ? 32 : (bitDepth === '16' ? 16 : 24);
      bytesPerSecond = rate * (depth / 8) * 2;
    }

    return Math.round(bytesPerSecond * duration);
  }, [selectedFormat, bitrate, oggQuality, bitDepth, sampleRate, audio, duration]);

  // Current output format badge info
  const outputSummaryLabel = useMemo(() => {
    const fmt = selectedFormat.toUpperCase();
    if (selectedFormat === 'original') return `Original (${audio?.codec || 'Opus'})`;
    if (['mp3', 'aac', 'm4a', 'opus'].includes(selectedFormat)) return `${fmt} • ${bitrate}`;
    if (selectedFormat === 'ogg') return `OGG • Q${oggQuality}`;
    if (selectedFormat === 'flac') return `FLAC • Lossless (${bitDepth === 'original' ? 'Source depth' : `${bitDepth}-bit`})`;
    if (selectedFormat === 'wav') return `WAV • ${bitDepth === 'original' ? '24-bit' : `${bitDepth}-bit`} PCM`;
    if (selectedFormat === 'alac') return `ALAC • Apple Lossless`;
    if (selectedFormat === 'aiff') return `AIFF • ${bitDepth}-bit PCM`;
    return fmt;
  }, [selectedFormat, bitrate, oggQuality, bitDepth, audio]);

  const handleStartConversion = () => {
    onConvertAudio({
      format: selectedFormat,
      quality_bitrate: bitrate,
      ogg_quality: oggQuality,
      sample_rate: sampleRate,
      bit_depth: bitDepth,
      compression_level: compressionLevel,
      channels: channels,
      normalize_audio: normalizeAudio,
      audio_format_id: audio?.format_id,
    });
  };

  const handleQuickOriginal = () => {
    onConvertAudio({
      format: 'original',
      channels: 'original',
      normalize_audio: false,
      audio_format_id: audio?.format_id,
    });
  };

  return (
    <div className="w-full max-w-5xl mx-auto px-4 space-y-6">
      
      {/* Quick Actions Header */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* Original Stream Extraction (Zero Loss) Card */}
        <div className="p-4 rounded-2xl bg-gradient-to-br from-cyan-950/40 to-slate-900/90 border border-cyan-800/60 shadow-xl flex flex-col justify-between space-y-3">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Zap className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                  Download Original Audio
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-300 font-mono">Stream Copy</span>
                </h3>
                <p className="text-xs text-slate-400">
                  Direct stream extraction without transcoding. Zero quality loss & fastest processing.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
            <div className="text-xs font-mono text-cyan-300">
              {audio ? `${audio.codec} • ${Math.round(audio.bitrate_kbps || 160)} kbps` : 'Source Stream'}
            </div>
            <button
              id="btn-download-original-audio"
              onClick={handleQuickOriginal}
              disabled={isProcessing}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold shadow-md shadow-cyan-500/25 transition-all disabled:opacity-50 cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Direct Extract</span>
            </button>
          </div>
        </div>

        {/* Best Available Recommendation Card */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col justify-between space-y-3">
          <div className="flex items-start gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                Smart Recommendation
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 font-mono">AI Suggest</span>
              </h3>
              <p className="text-xs text-slate-400">
                {audio?.codec?.toLowerCase().includes('opus')
                  ? 'Source is OPUS 160 kbps. Select OPUS 160k or MP3 320k for best fidelity.'
                  : 'Source is AAC/M4A. Select MP3 320k or M4A 256k for maximum universal playback.'}
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
            <span className="text-xs text-slate-400 font-medium">Universal Audio Suite</span>
            <button
              onClick={() => {
                setSelectedFormat('mp3');
                setBitrate('320k');
              }}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1 transition-colors cursor-pointer"
            >
              <span>Auto-Select MP3 320k</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>

      </div>

      {/* Main Converter Form Glass Panel */}
      <div className="glass-panel rounded-2xl p-5 sm:p-6 border border-slate-800 shadow-2xl space-y-6">
        
        {/* Section 1: Audio Format Selector Grid */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <Music className="w-4 h-4 text-cyan-400" />
              <span>1. Select Audio Format</span>
            </label>
            <span className="text-xs text-slate-400">9 studio-grade audio codecs</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-3 lg:grid-cols-5 gap-2.5">
            {media.supported_audio_formats.map((fmt) => {
              const isSelected = selectedFormat === fmt.format;
              return (
                <button
                  key={fmt.format}
                  id={`btn-format-${fmt.format}`}
                  type="button"
                  onClick={() => {
                    setSelectedFormat(fmt.format);
                    // Reset recommended bitrate per format
                    if (fmt.format === 'opus') setBitrate('160k');
                    else if (['aac', 'm4a'].includes(fmt.format)) setBitrate('256k');
                    else if (fmt.format === 'mp3') setBitrate('320k');
                  }}
                  className={`p-3 rounded-xl border text-left transition-all relative overflow-hidden cursor-pointer ${
                    isSelected
                      ? 'bg-cyan-950/60 border-cyan-500 ring-1 ring-cyan-500/50 shadow-lg shadow-cyan-500/15'
                      : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/60'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-sm text-white">{fmt.name}</span>
                    <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono font-medium ${
                      fmt.type === 'lossless'
                        ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                        : fmt.type === 'uncompressed'
                        ? 'bg-purple-950 text-purple-300 border border-purple-800'
                        : 'bg-slate-800 text-slate-400'
                    }`}>
                      {fmt.type}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-2 leading-tight">
                    {fmt.description}
                  </p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Section 2: Dynamic Format-Specific Quality Controls */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              <span>2. Audio Quality & Parameters</span>
            </span>
            <span className="text-xs font-mono text-cyan-400">
              Format: {selectedFormat.toUpperCase()}
            </span>
          </div>

          {/* MP3 Controls */}
          {selectedFormat === 'mp3' && (
            <div className="space-y-2">
              <label className="text-xs text-slate-400 font-medium">MP3 Bitrate (CBR)</label>
              <select
                id="select-bitrate-mp3"
                value={bitrate}
                onChange={(e) => setBitrate(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl p-3 focus:border-cyan-500 focus:outline-none"
              >
                {BITRATES_MP3.map((b) => (
                  <option key={b.value} value={b.value}>
                    {b.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* AAC / M4A Controls */}
          {['aac', 'm4a'].includes(selectedFormat) && (
            <div className="space-y-2">
              <label className="text-xs text-slate-400 font-medium">{selectedFormat.toUpperCase()} Bitrate</label>
              <select
                id="select-bitrate-aac"
                value={bitrate}
                onChange={(e) => setBitrate(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl p-3 focus:border-cyan-500 focus:outline-none"
              >
                {BITRATES_AAC.map((b) => (
                  <option key={b.value} value={b.value}>
                    {b.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* OPUS Controls */}
          {selectedFormat === 'opus' && (
            <div className="space-y-2">
              <label className="text-xs text-slate-400 font-medium">OPUS Bitrate</label>
              <select
                id="select-bitrate-opus"
                value={bitrate}
                onChange={(e) => setBitrate(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl p-3 focus:border-cyan-500 focus:outline-none"
              >
                {BITRATES_OPUS.map((b) => (
                  <option key={b.value} value={b.value}>
                    {b.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* OGG Vorbis Quality Controls */}
          {selectedFormat === 'ogg' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-xs text-slate-400 font-medium">Vorbis Quality Setting (VBR)</label>
                <span className="text-xs font-mono font-bold text-cyan-300">Level {oggQuality}</span>
              </div>
              <select
                id="select-ogg-quality"
                value={oggQuality}
                onChange={(e) => setOggQuality(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl p-3 focus:border-cyan-500 focus:outline-none"
              >
                {OGG_VORBIS_LEVELS.map((lvl) => (
                  <option key={lvl.value} value={lvl.value}>
                    {lvl.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* FLAC Lossless Controls */}
          {selectedFormat === 'flac' && (
            <div className="space-y-3">
              <div className="p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 text-xs flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>FLAC Lossless encoding: Full waveform preservation without lossy degradation.</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-medium">Bit Depth</label>
                  <select
                    value={bitDepth}
                    onChange={(e) => setBitDepth(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl p-2.5"
                  >
                    <option value="original">Original Depth</option>
                    <option value="16">16-bit (CD Quality)</option>
                    <option value="24">24-bit (Hi-Res Master)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-medium">Sample Rate</label>
                  <select
                    value={sampleRate}
                    onChange={(e) => setSampleRate(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl p-2.5"
                  >
                    {SAMPLE_RATES.map((sr) => (
                      <option key={sr.value} value={sr.value}>
                        {sr.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-medium">Compression Level</label>
                  <select
                    value={compressionLevel}
                    onChange={(e) => setCompressionLevel(Number(e.target.value))}
                    className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl p-2.5"
                  >
                    <option value={0}>0 — Fastest</option>
                    <option value={3}>3 — Light</option>
                    <option value={5}>5 — Default (Balanced)</option>
                    <option value={8}>8 — Maximum Compression</option>
                  </select>
                </div>
              </div>

              <p className="text-[11px] text-slate-400 italic">
                * Note: FLAC compression level affects file size and CPU encoding speed, NEVER audio quality.
              </p>
            </div>
          )}

          {/* WAV Uncompressed Studio Controls */}
          {selectedFormat === 'wav' && (
            <div className="space-y-3">
              <div className="p-2.5 rounded-lg bg-purple-950/40 border border-purple-800/60 text-purple-300 text-xs flex items-center gap-2">
                <Music className="w-4 h-4 text-purple-400 shrink-0" />
                <span>WAV Uncompressed PCM: Pure raw studio samples without container compression.</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-medium">PCM Bit Depth</label>
                  <select
                    value={bitDepth}
                    onChange={(e) => setBitDepth(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl p-2.5"
                  >
                    <option value="24">24-bit PCM (Recommended)</option>
                    <option value="16">16-bit PCM (CD Standard)</option>
                    <option value="32_float">32-bit Float (DAW Workstations)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs text-slate-400 block mb-1.5 font-medium">Sample Rate</label>
                  <select
                    value={sampleRate}
                    onChange={(e) => setSampleRate(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl p-2.5"
                  >
                    {SAMPLE_RATES.map((sr) => (
                      <option key={sr.value} value={sr.value}>
                        {sr.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* ALAC / AIFF Controls */}
          {['alac', 'aiff'].includes(selectedFormat) && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-slate-400 block mb-1.5 font-medium">Bit Depth</label>
                <select
                  value={bitDepth}
                  onChange={(e) => setBitDepth(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl p-2.5"
                >
                  <option value="16">16-bit</option>
                  <option value="24">24-bit (High Quality)</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-slate-400 block mb-1.5 font-medium">Sample Rate</label>
                <select
                  value={sampleRate}
                  onChange={(e) => setSampleRate(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl p-2.5"
                >
                  {SAMPLE_RATES.map((sr) => (
                    <option key={sr.value} value={sr.value}>
                      {sr.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

        </div>

        {/* Section 3: Conversion Inspector & Warning Banner */}
        <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
            
            {/* Input -> Output Comparison Flow */}
            <div className="flex items-center gap-3">
              <div className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700">
                <span className="text-slate-500 text-[10px] block uppercase font-mono">Input Source</span>
                <span className="font-mono font-bold text-slate-200">
                  {audio?.codec || 'Opus'} • {audio?.bitrate_kbps ? `${Math.round(audio.bitrate_kbps)} kbps` : '48 kHz'}
                </span>
              </div>

              <ArrowRight className="w-4 h-4 text-cyan-400" />

              <div className="px-3 py-1.5 rounded-lg bg-cyan-950 border border-cyan-700 text-cyan-300">
                <span className="text-cyan-400 text-[10px] block uppercase font-mono">Target Output</span>
                <span className="font-mono font-bold">
                  {outputSummaryLabel}
                </span>
              </div>
            </div>

            {/* Estimated Size Pill */}
            <div className="text-right">
              <span className="text-slate-500 text-[10px] block uppercase font-mono">Estimated File Size</span>
              <span className="font-mono font-bold text-white text-sm">
                {formatBytes(estimatedOutputSize)}
              </span>
            </div>

          </div>

          {/* Upsampling Warning Alert */}
          {isUpsamplingWarning && (
            <div className="p-3 rounded-lg bg-amber-950/30 border border-amber-800/60 flex items-start gap-2.5 text-amber-300 text-xs animate-in fade-in duration-200">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold">Audio Upsampling Note: </span>
                <span>
                  Converting a lower-quality source to a higher bitrate will increase file size but cannot restore audio information that is missing from the original stream.
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Section 4: Advanced Audio Settings Collapsible */}
        <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950/40">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="w-full p-3.5 flex items-center justify-between text-xs font-semibold text-slate-300 hover:text-white transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <Sliders className="w-3.5 h-3.5 text-cyan-400" />
              <span>Advanced Audio Engineering Options (Channels & Normalization)</span>
            </div>
            <span className="text-[11px] text-cyan-400">{showAdvanced ? 'Hide' : 'Show'}</span>
          </button>

          {showAdvanced && (
            <div className="p-4 pt-0 border-t border-slate-800/60 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs pt-3 animate-in fade-in duration-200">
              
              {/* Channel Layout */}
              <div>
                <label className="text-slate-400 block mb-1.5 font-medium">Audio Channels</label>
                <select
                  value={channels}
                  onChange={(e) => setChannels(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl p-2.5"
                >
                  <option value="original">Original (Keep Source Channels)</option>
                  <option value="stereo">Stereo (2 Channels)</option>
                  <option value="mono">Mono (1 Channel - Voice/Speech)</option>
                </select>
              </div>

              {/* Loudness Normalization */}
              <div>
                <label className="text-slate-400 block mb-1.5 font-medium">Loudness Normalization</label>
                <label className="flex items-center gap-2.5 p-2.5 rounded-xl bg-slate-900 border border-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={normalizeAudio}
                    onChange={(e) => setNormalizeAudio(e.target.checked)}
                    className="w-4 h-4 rounded border-slate-700 text-cyan-500 focus:ring-cyan-500 bg-slate-800"
                  />
                  <span className="text-slate-300 text-xs">
                    Normalize Audio (EBU R128 standard)
                  </span>
                </label>
              </div>

            </div>
          )}
        </div>

        {/* Section 5: Submit Action Button */}
        <div className="pt-2">
          <button
            id="btn-convert-and-download-audio"
            onClick={handleStartConversion}
            disabled={isProcessing}
            className="w-full flex items-center justify-center gap-2.5 py-4 rounded-xl bg-gradient-to-r from-cyan-500 via-indigo-600 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white font-bold text-sm shadow-xl shadow-cyan-500/25 transition-all disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-4 h-4 ${isProcessing ? 'animate-spin' : ''}`} />
            <span>Convert & Download Audio ({selectedFormat.toUpperCase()})</span>
          </button>
        </div>

      </div>

    </div>
  );
}
