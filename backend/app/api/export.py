from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import datetime
import json

from core.config import settings
from core.security import verify_token, session_manager

router = APIRouter()


class ExportData(BaseModel):
    session_info: Dict[str, Any]
    documents: List[Dict[str, Any]]
    conversations: List[Dict[str, Any]]
    export_timestamp: str
    session_duration_hours: float


@router.get("/all", response_model=ExportData)
async def export_all_data(token_data: Dict[str, Any] = Depends(verify_token)) -> ExportData:
    """Export all session data as JSON"""

    session_id = token_data.get("session_id")
    username = token_data.get("sub")

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )

    session_data = session_manager.get_session(session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Calculate session duration
    time_remaining = session_manager.get_session_time_remaining(session_id)
    if time_remaining:
        hours_used = settings.SESSION_TTL_HOURS - (time_remaining.total_seconds() / 3600)
    else:
        hours_used = settings.SESSION_TTL_HOURS

    # Prepare export data
    export_data = {
        "session_info": {
            "username": username,
            "session_id": session_id,
            "created_at": session_data.get("created_at", "").isoformat() if session_data.get("created_at") else "",
            "session_ttl_hours": settings.SESSION_TTL_HOURS,
            "hours_used": round(hours_used, 2)
        },
        "documents": [
            {
                "filename": doc["filename"],
                "size_bytes": doc["size_bytes"],
                "upload_time": doc["upload_time"],
                "file_type": doc["file_type"],
                "document_id": doc["document_id"]
            }
            for doc in session_data.get("documents", [])
        ],
        "conversations": session_data.get("conversations", []),
        "export_timestamp": datetime.utcnow().isoformat(),
        "session_duration_hours": round(hours_used, 2)
    }

    return ExportData(**export_data)


@router.get("/download")
async def download_export(token_data: Dict[str, Any] = Depends(verify_token)):
    """Download all session data as a JSON file"""

    # Get export data
    export_data = await export_all_data(token_data)

    # Convert to JSON string
    _json_content = json.dumps(export_data.dict(), indent=2, default=str)

    # Create filename with timestamp
    filename = f"legal_ai_sandbox_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    # Return as downloadable file
    return JSONResponse(
        content=export_data.dict(),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
