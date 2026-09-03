import asyncio
import logging
from fastapi import APIRouter, HTTPException, status
from backend.models.requests import AnalyzeRequest
from backend.models.media import MediaInfo
from backend.utils.security import validate_url_security
from backend.services.extractor import (
    analyze_media_url, ExtractorError, MediaRestrictedError
)
from backend.services.media_analyzer import parse_media_info

logger = logging.getLogger("mediaflow.api.analyze")
router = APIRouter(prefix="/api", tags=["Analyze"])

@router.post("/analyze", response_model=MediaInfo)
async def analyze_url(req: AnalyzeRequest):
    """
    Analyzes a video URL, extracts metadata, video stream formats, and audio information.
    Enforces SSRF validation and DRM/restricted media checks.
    """
    url = req.url.strip()
    
    # 1. SSRF & URL Validation
    is_valid, error_msg = validate_url_security(url)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # 2. Extract and Parse Media Info
    try:
        raw_info = await asyncio.to_thread(analyze_media_url, url)
        media_info = parse_media_info(raw_info, url)
        return media_info
        
    except MediaRestrictedError as e:
        logger.warning(f"Restricted media request for {url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ExtractorError as e:
        logger.info(f"Extractor error for {url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during media analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while analyzing the media. Please try again later."
        )
