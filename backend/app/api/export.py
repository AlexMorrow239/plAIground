from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import datetime, timezone
import json
import zipfile
from io import BytesIO

from app.core.config import settings
from app.core.security import verify_token, session_manager
from app.core.database import ephemeral_db

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

    # Get conversations from the ephemeral database
    db_conversations = ephemeral_db.get_conversations_for_session(session_id)

    # Format conversations for export
    formatted_conversations = []
    for conv in db_conversations:
        formatted_messages = []
        for msg in conv["messages"]:
            formatted_msg = {
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"],
                "document_ids": msg.get("document_ids", [])
            }
            # Only include document references, not full contents
            if msg.get("document_contents"):
                formatted_msg["attached_documents"] = [
                    doc_data["filename"]
                    for doc_data in msg["document_contents"].values()
                ]
            formatted_messages.append(formatted_msg)

        formatted_conversations.append({
            "conversation_id": conv["conversation_id"],
            "created_at": conv["created_at"],
            "messages": formatted_messages
        })

    # Get documents from the ephemeral database
    db_documents = ephemeral_db.get_documents_for_session(session_id)

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
                "size_bytes": doc["file_size"],
                "upload_time": doc["uploaded_at"],
                "file_type": doc["file_type"],
                "document_id": doc["id"],
                "page_count": doc.get("page_count"),
                "word_count": doc.get("word_count")
            }
            for doc in db_documents
        ],
        "conversations": formatted_conversations,
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
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
    filename = f"legal_ai_sandbox_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"

    # Return as downloadable file
    return JSONResponse(
        content=export_data.dict(),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/zip")
async def export_as_zip(token_data: Dict[str, Any] = Depends(verify_token)):
    """Export all session data as a ZIP file containing text files for each conversation"""

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

    # Get conversations from the ephemeral database
    db_conversations = ephemeral_db.get_conversations_for_session(session_id)

    # Create in-memory ZIP file
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add session info file
        session_info_content = f"""Legal AI Research Sandbox Export
=====================================
Session ID: {session_id}
Username: {username}
Exported: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
Session TTL: {settings.SESSION_TTL_HOURS} hours
=====================================

This export contains {len(db_conversations)} conversation(s).
"""
        zip_file.writestr("session_info.txt", session_info_content)

        # Add each conversation as a separate text file
        for conv in db_conversations:
            # Parse conversation created date
            created_date = datetime.fromisoformat(conv["created_at"].replace('Z', '+00:00'))
            conv_date_str = created_date.strftime('%Y%m%d_%H%M%S')

            # Build conversation text content
            conv_content = []
            conv_content.append(f"Conversation ID: {conv['conversation_id']}")
            conv_content.append(f"Created: {created_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            conv_content.append("=" * 50)
            conv_content.append("")

            # Add each message
            for msg in conv["messages"]:
                # Parse message timestamp
                msg_time = datetime.fromisoformat(msg["timestamp"].replace('Z', '+00:00'))
                time_str = msg_time.strftime('%H:%M:%S')

                # Format role for display
                role_display = "User" if msg["role"] == "user" else "Assistant"

                # Build message header
                conv_content.append(f"[{time_str}] {role_display}:")

                # Add document references if present
                if msg.get("document_contents"):
                    doc_filenames = [
                        doc_data["filename"]
                        for doc_data in msg["document_contents"].values()
                    ]
                    if doc_filenames:
                        conv_content.append(f"[Attached: {', '.join(doc_filenames)}]")

                # Add message content
                conv_content.append(msg["content"])
                conv_content.append("")  # Empty line between messages

            # Create filename for this conversation
            filename = f"conversation_{conv['conversation_id']}_{conv_date_str}.txt"

            # Add conversation to ZIP
            zip_file.writestr(filename, "\n".join(conv_content))

        # Add document list file if there are documents
        db_documents = ephemeral_db.get_documents_for_session(session_id)
        if db_documents:
            doc_list_content = ["Document List", "=" * 50, ""]

            for doc in db_documents:
                doc_list_content.append(f"Filename: {doc['filename']}")
                doc_list_content.append(f"  Document ID: {doc['id']}")
                doc_list_content.append(f"  File Type: {doc['file_type']}")
                doc_list_content.append(f"  Size: {doc['file_size']:,} bytes")
                doc_list_content.append(f"  Uploaded: {doc['uploaded_at']}")

                if doc.get("page_count"):
                    doc_list_content.append(f"  Pages: {doc['page_count']}")
                if doc.get("word_count"):
                    doc_list_content.append(f"  Words: {doc['word_count']:,}")
                if doc.get("processing_error"):
                    doc_list_content.append(f"  Error: {doc['processing_error']}")

                doc_list_content.append("")  # Empty line between documents

            zip_file.writestr("document_list.txt", "\n".join(doc_list_content))

    # Prepare ZIP for download
    zip_buffer.seek(0)

    # Create filename with timestamp
    filename = f"legal_ai_sandbox_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"

    # Return ZIP file as streaming response
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
