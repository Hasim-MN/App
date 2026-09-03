import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.services.ffmpeg_service import ensure_ffmpeg_initialized
from backend.utils.files import periodic_temp_cleanup
from backend.api.analyze import router as analyze_router
from backend.api.download import router as download_router
from backend.api.jobs import router as jobs_router
from backend.api.health import router as health_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("mediaflow.main")

async def cleanup_task():
    """Background task to periodically clean up expired job files."""
    while True:
        try:
            await asyncio.sleep(settings.CLEANUP_INTERVAL_SECONDS)
            cleaned = periodic_temp_cleanup()
            if cleaned > 0:
                logger.info(f"Periodic cleanup removed {cleaned} expired job folder(s).")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error during periodic cleanup task: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing MediaFlow Downloader backend...")
    ffmpeg_ready = ensure_ffmpeg_initialized()
    if ffmpeg_ready:
        logger.info("FFmpeg and FFprobe verified and ready.")
    else:
        logger.warning("FFmpeg / FFprobe not found or failed to initialize!")
        
    cleanup_bg_task = asyncio.create_task(cleanup_task())
    
    yield
    
    # Shutdown
    cleanup_bg_task.cancel()
    logger.info("MediaFlow Downloader backend shutdown complete.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Modern Full-Stack Media Inspection, Conversion, and Download Service",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(analyze_router)
app.include_router(download_router)
app.include_router(jobs_router)
app.include_router(health_router)

@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
