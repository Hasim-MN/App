'use client';

import React, { useState, useEffect } from 'react';
import { X, History, Download, Trash2, ExternalLink, Clock, HardDrive, CheckCircle2 } from 'lucide-react';
import { JobHistoryItem } from '@/lib/types';
import { getJobHistory, getDownloadUrl } from '@/lib/api';
import { formatBytes } from '@/lib/utils';

interface HistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectUrl?: (url: string) => void;
}

export default function HistoryDrawer({ isOpen, onClose, onSelectUrl }: HistoryDrawerProps) {
  const [historyItems, setHistoryItems] = useState<JobHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const serverHistory = await getJobHistory();
      // Also merge with localStorage items if available
      const local = localStorage.getItem('mediaflow_local_history');
      let localItems: JobHistoryItem[] = [];
      if (local) {
        try {
          localItems = JSON.parse(local);
        } catch {
          // ignore
        }
      }

      // Merge and deduplicate by job_id
      const combined = [...localItems, ...serverHistory];
      const seen = new Set<string>();
      const deduped = combined.filter((item) => {
        if (!item.job_id || seen.has(item.job_id)) return false;
        seen.add(item.job_id);
        return true;
      });

      // Sort newest first
      deduped.sort((a, b) => b.completed_at - a.completed_at);
      setHistoryItems(deduped);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadHistory();
    }
  }, [isOpen]);

  const clearHistory = () => {
    localStorage.removeItem('mediaflow_local_history');
    setHistoryItems([]);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="w-full max-w-md h-full bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col animate-in slide-in-from-right duration-300"
      >
        
        {/* Drawer Header */}
        <div className="p-4 sm:p-6 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">Recent Conversions</h3>
              <p className="text-xs text-slate-400">Session and completed downloads history</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Action Toolbar */}
        {historyItems.length > 0 && (
          <div className="px-6 py-2.5 bg-slate-950/40 border-b border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span>{historyItems.length} item{historyItems.length !== 1 ? 's' : ''}</span>
            <button
              onClick={clearHistory}
              className="flex items-center gap-1 text-slate-400 hover:text-rose-400 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear History</span>
            </button>
          </div>
        )}

        {/* History List */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-3">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-48 text-slate-400 space-y-2">
              <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-xs">Loading history...</p>
            </div>
          ) : historyItems.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-center text-slate-400 space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-slate-800/50 border border-slate-700/50 flex items-center justify-center text-slate-500">
                <History className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-300">No download history yet</p>
                <p className="text-xs text-slate-500 mt-0.5">
                  Completed audio conversions and video merges will appear here.
                </p>
              </div>
            </div>
          ) : (
            historyItems.map((item) => (
              <div
                key={item.job_id}
                className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition-all space-y-2"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <h4 className="text-xs font-semibold text-white truncate" title={item.title}>
                      {item.title}
                    </h4>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-800/60 font-medium">
                        {item.format_type}
                      </span>
                      {item.file_size_bytes && (
                        <span className="text-[11px] text-slate-400 flex items-center gap-1">
                          <HardDrive className="w-3 h-3 text-slate-500" />
                          {formatBytes(item.file_size_bytes)}
                        </span>
                      )}
                    </div>
                  </div>

                  <a
                    href={getDownloadUrl(item.job_id)}
                    download={item.file_name}
                    className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500 hover:text-white border border-cyan-500/20 transition-all shrink-0"
                    title="Download file again"
                  >
                    <Download className="w-4 h-4" />
                  </a>
                </div>

                <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-500">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(item.completed_at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <span className="truncate max-w-[180px] font-mono">{item.file_name}</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer Note */}
        <div className="p-4 border-t border-slate-800 text-center text-xs text-slate-500">
          Temporary server files are retained for up to 30 minutes.
        </div>

      </div>
    </div>
  );
}
