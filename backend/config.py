import os
import tempfile
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "MediaFlow Downloader"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]
    
    # Storage and temp directories
    BASE_TEMP_DIR: str = os.path.join(tempfile.gettempdir(), "mediaflow")
    
    # Resource limits
    MAX_FILE_SIZE_BYTES: int = 2 * 1024 * 1024 * 1024  # 2 GB
    MAX_CONCURRENT_JOBS: int = 10
    JOB_TIMEOUT_SECONDS: int = 600  # 10 minutes
    JOB_RETENTION_SECONDS: int = 1800  # 30 minutes before deletion of temp files
    CLEANUP_INTERVAL_SECONDS: int = 300  # 5 minutes
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = 60
    
    # Supported protocols
    ALLOWED_PROTOCOLS: list[str] = ["http", "https"]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure base temp dir exists
Path(settings.BASE_TEMP_DIR).mkdir(parents=True, exist_ok=True)
