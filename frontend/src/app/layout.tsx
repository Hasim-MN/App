import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'MediaFlow Downloader — Modern Video Inspector & Audio Converter',
  description: 'Analyze media streams, download high-definition video formats with FFmpeg stream copying, and convert audio into MP3, FLAC, WAV, AAC, M4A, OGG, OPUS, ALAC, and AIFF.',
  keywords: ['media downloader', 'video inspector', 'audio converter', 'ffmpeg stream merge', 'flac converter', 'mp3 320k', 'mediaflow'],
  authors: [{ name: 'MediaFlow Team' }],
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased min-h-screen bg-[#07090e] text-slate-100 flex flex-col selection:bg-cyan-500/30 selection:text-cyan-200">
        {children}
      </body>
    </html>
  );
}
