import { MediaInfo, JobProgress, SystemHealth, JobHistoryItem } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function analyzeUrl(url: string): Promise<MediaInfo> {
  const response = await fetch(`${API_BASE}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to analyze media URL');
  }

  return data;
}

export async function startVideoDownload(payload: {
  url: string;
  format_id: string;
  container?: string;
  audio_format_id?: string;
  title?: string;
  thumbnail?: string;
}): Promise<{ job_id: string; stream_url: string; status_url: string }> {
  const response = await fetch(`${API_BASE}/api/download/video`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to start video download');
  }

  return data;
}

export async function startAudioDownload(payload: {
  url: string;
  format: string;
  quality_bitrate?: string;
  ogg_quality?: number;
  sample_rate?: string;
  bit_depth?: string;
  compression_level?: number;
  channels?: string;
  normalize_audio?: boolean;
  audio_format_id?: string;
  title?: string;
  thumbnail?: string;
}): Promise<{ job_id: string; stream_url: string; status_url: string }> {
  const response = await fetch(`${API_BASE}/api/download/audio`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to start audio conversion');
  }

  return data;
}

export async function getJobStatus(jobId: string): Promise<JobProgress> {
  const response = await fetch(`${API_BASE}/api/jobs/${jobId}`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to fetch job status');
  }
  return data;
}

export async function getHealth(): Promise<SystemHealth> {
  const response = await fetch(`${API_BASE}/api/health`);
  if (!response.ok) {
    throw new Error('Health check failed');
  }
  return response.json();
}

export async function getJobHistory(): Promise<JobHistoryItem[]> {
  try {
    const response = await fetch(`${API_BASE}/api/jobs/history`);
    if (response.ok) {
      return response.json();
    }
  } catch {
    // Ignore error
  }
  return [];
}

export function getDownloadUrl(jobId: string): string {
  return `${API_BASE}/api/jobs/${jobId}/download`;
}

/**
 * Connects to SSE stream for real-time progress, with automatic polling fallback.
 */
export function subscribeToJobProgress(
  jobId: string,
  onProgress: (progress: JobProgress) => void,
  onComplete: (progress: JobProgress) => void,
  onError: (error: string) => void
): () => void {
  let isClosed = false;
  let eventSource: EventSource | null = null;
  let pollingInterval: NodeJS.Timeout | null = null;

  const handleUpdate = (progress: JobProgress) => {
    onProgress(progress);
    if (progress.status === 'COMPLETED') {
      cleanup();
      onComplete(progress);
    } else if (progress.status === 'FAILED' || progress.status === 'CANCELLED') {
      cleanup();
      onError(progress.error || 'Job processing failed');
    }
  };

  const startPolling = () => {
    if (pollingInterval || isClosed) return;
    pollingInterval = setInterval(async () => {
      try {
        const progress = await getJobStatus(jobId);
        handleUpdate(progress);
      } catch (err: any) {
        if (!isClosed) {
          onError(err.message || 'Error checking job status');
          cleanup();
        }
      }
    }, 1000);
  };

  const cleanup = () => {
    isClosed = true;
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
    if (pollingInterval) {
      clearInterval(pollingInterval);
      pollingInterval = null;
    }
  };

  try {
    eventSource = new EventSource(`${API_BASE}/api/jobs/${jobId}/stream`);

    eventSource.addEventListener('progress', (e: MessageEvent) => {
      if (isClosed) return;
      try {
        const data: JobProgress = JSON.parse(e.data);
        handleUpdate(data);
      } catch (err) {
        console.error('Error parsing SSE event:', err);
      }
    });

    eventSource.onerror = () => {
      // Fallback to polling on SSE error
      if (!isClosed) {
        if (eventSource) {
          eventSource.close();
          eventSource = null;
        }
        startPolling();
      }
    };
  } catch {
    startPolling();
  }

  return cleanup;
}
