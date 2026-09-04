'use client';

import React, { useState, useEffect } from 'react';
import { X, Server, CheckCircle2, AlertCircle, RefreshCw, Smartphone, Globe } from 'lucide-react';
import { getApiBaseUrl, setApiBaseUrl, getHealth } from '@/lib/api';

interface ServerSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onServerUpdated?: () => void;
}

export default function ServerSettingsModal({
  isOpen,
  onClose,
  onServerUpdated,
}: ServerSettingsModalProps) {
  const [serverUrl, setServerUrl] = useState('');
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [testMessage, setTestMessage] = useState('');

  useEffect(() => {
    if (isOpen) {
      setServerUrl(getApiBaseUrl());
      setTestStatus('idle');
      setTestMessage('');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleTestConnection = async (urlToTest: string) => {
    setTestStatus('testing');
    setTestMessage('Connecting to backend...');
    try {
      const cleanUrl = urlToTest.trim().replace(/\/+$/, '');
      const res = await fetch(`${cleanUrl}/api/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: Server returned error`);
      }
      const data = await res.json();
      if (data.status === 'ok') {
        setTestStatus('success');
        setTestMessage(`Connected! Engine: ${data.dependencies?.ffmpeg?.available ? 'FFmpeg Ready' : 'Online'}`);
      } else {
        setTestStatus('error');
        setTestMessage('Server responded but health status was degraded');
      }
    } catch (err: any) {
      setTestStatus('error');
      setTestMessage(err.message || 'Cannot reach server. Verify IP/port and firewall settings.');
    }
  };

  const handleSave = () => {
    const cleanUrl = serverUrl.trim().replace(/\/+$/, '');
    setApiBaseUrl(cleanUrl);
    if (onServerUpdated) {
      onServerUpdated();
    }
    onClose();
  };

  const handleResetDefault = () => {
    const defaultUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/+$/, '');
    setServerUrl(defaultUrl);
    setApiBaseUrl('');
    handleTestConnection(defaultUrl);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-md rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl p-6 overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-950/80 border border-cyan-800/60 text-cyan-400">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-white text-base">Backend API Server</h3>
              <p className="text-xs text-slate-400">Configure connection for Android or Web</p>
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
        <div className="py-4 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              API Server Base URL
            </label>
            <div className="relative">
              <input
                type="text"
                value={serverUrl}
                onChange={(e) => {
                  setServerUrl(e.target.value);
                  setTestStatus('idle');
                }}
                placeholder="http://192.168.1.5:8000 or https://api.yourdomain.com"
                className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 focus:border-cyan-500 focus:outline-none text-sm text-white font-mono placeholder-slate-600 transition-all"
              />
              <Globe className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
            </div>
          </div>

          {/* Quick Presets */}
          <div className="space-y-1.5">
            <span className="text-[11px] font-medium text-slate-400">Quick URL Presets:</span>
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() => {
                  setServerUrl('http://172.21.144.47:8000');
                  setTestStatus('idle');
                }}
                className="px-2.5 py-1 rounded-lg bg-cyan-950/60 border border-cyan-800/80 hover:border-cyan-400 text-[11px] text-cyan-300 font-medium transition-colors"
              >
                Local Wi-Fi PC (172.21.144.47)
              </button>
              <button
                type="button"
                onClick={() => {
                  setServerUrl('http://localhost:8000');
                  setTestStatus('idle');
                }}
                className="px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 hover:border-cyan-500/50 text-[11px] text-slate-300 transition-colors"
              >
                Localhost (PC)
              </button>
              <button
                type="button"
                onClick={() => {
                  setServerUrl('http://10.0.2.2:8000');
                  setTestStatus('idle');
                }}
                className="px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 hover:border-cyan-500/50 text-[11px] text-slate-300 transition-colors"
              >
                Android Emulator
              </button>
            </div>
          </div>

          {/* Android Mobile & Background Guidance */}
          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs text-slate-300 space-y-2">
            <div className="flex items-center gap-2 font-medium text-cyan-400">
              <Smartphone className="w-4 h-4 shrink-0" />
              <span>Mobile & Server Setup Guide:</span>
            </div>
            <div className="space-y-1.5 text-[11px] text-slate-400 leading-relaxed">
              <p>
                • <strong className="text-cyan-300">Recommended for YouTube (Local Wi-Fi):</strong> Cloud hosts (Render/AWS) have their IP addresses blocked by YouTube. Connect your phone to your PC on the same Wi-Fi using <code className="text-cyan-300 bg-cyan-950/70 px-1 py-0.5 rounded font-mono">http://172.21.144.47:8000</code>.
              </p>
              <p>
                • <strong className="text-slate-200">Terminal closed error?</strong> Closing your command prompt kills the local backend. Double-click <code className="text-cyan-300 bg-cyan-950/70 px-1 py-0.5 rounded">scripts/start_backend_background.vbs</code> on your PC to run it silently in the background with zero open windows!
              </p>
              <p>
                • <strong className="text-slate-200">Cloud Hosting (Render):</strong> If using Render, YouTube may require cookies or local residential IP routing. Non-YouTube sources (Instagram, Twitter, Facebook, TikTok, etc.) work anywhere 24/7 on Render.
              </p>
            </div>
          </div>

          {/* Test Status Banner */}
          {testStatus !== 'idle' && (
            <div
              className={`p-3 rounded-xl border text-xs flex items-start gap-2.5 transition-all ${
                testStatus === 'testing'
                  ? 'bg-slate-950 border-slate-800 text-slate-300'
                  : testStatus === 'success'
                  ? 'bg-emerald-950/50 border-emerald-800/60 text-emerald-300'
                  : 'bg-rose-950/50 border-rose-800/60 text-rose-300'
              }`}
            >
              {testStatus === 'testing' && <RefreshCw className="w-4 h-4 text-cyan-400 animate-spin shrink-0 mt-0.5" />}
              {testStatus === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />}
              {testStatus === 'error' && <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />}
              <span className="leading-relaxed">{testMessage}</span>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={handleResetDefault}
              className="text-xs text-slate-400 hover:text-slate-200 underline transition-colors"
            >
              Reset Default
            </button>
            <button
              type="button"
              onClick={() => handleTestConnection(serverUrl)}
              disabled={testStatus === 'testing'}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${testStatus === 'testing' ? 'animate-spin' : ''}`} />
              <span>Test Connection</span>
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-2.5">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white shadow-lg shadow-cyan-500/20 transition-all"
          >
            Save & Connect
          </button>
        </div>

      </div>
    </div>
  );
}
