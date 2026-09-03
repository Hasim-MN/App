# Multi-stage production Dockerfile for MediaFlow Downloader

# Stage 1: Build Frontend Next.js
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 2: Production Runtime with Python & FFmpeg
FROM python:3.11-slim

# Install system dependencies & FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Create non-root application user
RUN useradd -m -u 1001 mediaflow

WORKDIR /app

# Install Python backend dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public
COPY --from=frontend-builder /app/frontend/package*.json ./frontend/
COPY --from=frontend-builder /app/frontend/node_modules ./frontend/node_modules

# Set ownership to non-root user
RUN chown -R mediaflow:mediaflow /app /tmp

USER mediaflow

# Expose backend (8000) and frontend (3000)
EXPOSE 8000 3000

ENV HOST=0.0.0.0
ENV PORT=8000

# Start script
CMD ["sh", "-c", "cd /app/frontend && npm run start & uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
