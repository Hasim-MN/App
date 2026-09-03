export interface VideoFormat {
  format_id: string;
  extension: string;
  quality_label: string;
  resolution: string;
  width?: number;
  height?: number;
  fps?: number;
  video_codec?: string;
  audio_codec?: string;
  bitrate_kbps?: number;
  estimated_size_bytes?: number;
  has_video: boolean;
  has_audio: boolean;
  is_dash_video: boolean;
  audio_format_id_for_merge?: string;
}

export interface OriginalAudioSpecs {
  codec: string;
  bitrate_kbps?: number;
  sample_rate_hz?: number;
  channels?: number;
  channel_layout?: string;
  bit_depth?: number;
  estimated_size_bytes?: number;
  format_id?: string;
  extension?: string;
}

export interface AudioFormatOption {
  format: string;
  name: string;
  type: 'lossy' | 'lossless' | 'uncompressed';
  description: string;
  recommended_quality: string;
  default_extension: string;
}

export interface MediaInfo {
  url: string;
  title: string;
  thumbnail?: string;
  duration_seconds?: number;
  duration_formatted: string;
  source: string;
  uploader?: string;
  view_count?: number;
  upload_date?: string;
  description?: string;
  video_formats: VideoFormat[];
  original_audio?: OriginalAudioSpecs;
  supported_audio_formats: AudioFormatOption[];
}

export type JobStatusType = 'QUEUED' | 'PREPARING' | 'DOWNLOADING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export interface JobProgress {
  job_id: string;
  status: JobStatusType;
  phase: string;
  percent: number;
  speed_str?: string;
  eta_str?: string;
  downloaded_bytes?: number;
  total_bytes?: number;
  file_name?: string;
  file_size_bytes?: number;
  media_title?: string;
  media_thumbnail?: string;
  selected_format?: string;
  output_path?: string;
  error?: string;
  created_at: number;
  updated_at: number;
  download_url?: string;
}

export interface JobHistoryItem {
  job_id: string;
  title: string;
  thumbnail?: string;
  format_type: string;
  selected_quality: string;
  file_size_bytes?: number;
  completed_at: number;
  file_name: string;
}

export interface SystemHealth {
  status: string;
  app_name: string;
  app_version: string;
  dependencies: {
    ffmpeg: { available: boolean; version?: string };
    ffprobe: { available: boolean; version?: string };
    yt_dlp: { available: boolean; version?: string };
  };
  limits: {
    max_file_size_gb: number;
    max_concurrent_jobs: number;
    job_retention_minutes: number;
  };
}
