"""Health check endpoints."""
from typing import Dict
from fastapi import APIRouter
import httpx
from app.core.config import settings

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/ollama")
async def check_ollama_health() -> Dict[str, bool]:
    """
    Check if Ollama service is available and responding.

    Returns:
        Dict with 'available' key indicating if Ollama is reachable
    """
    try:
        async with httpx.AsyncClient() as client:
            # Make a simple request to Ollama's API endpoint
            response = await client.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags",
                timeout=5.0  # 5 second timeout for health check
            )
            response.raise_for_status()
            return {"available": True}
    except (httpx.HTTPError, httpx.TimeoutException):
        return {"available": False}
