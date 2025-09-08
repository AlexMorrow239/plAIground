from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import shutil
from datetime import datetime
import hashlib

from app.core.config import settings
from app.core.security import verify_token, session_manager

router = APIRouter()


class DocumentInfo(BaseModel):
    filename: str
    size_bytes: int
    size_mb: float
    upload_time: str
    file_type: str
    document_id: str


@router.post("/upload", response_model=DocumentInfo)
async def upload_document(
    file: UploadFile = File(...),
    token_data: Dict[str, Any] = Depends(verify_token)
) -> DocumentInfo:
    """Upload a document to temporary storage"""
    
    # Validate file type
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_extension} not allowed. Allowed types: {settings.ALLOWED_FILE_TYPES}"
        )
    
    # Check file size
    file_size = 0
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Generate document ID
    doc_id = hashlib.md5(f"{file.filename}{datetime.utcnow()}".encode()).hexdigest()
    
    # Create upload directory if it doesn't exist (in tmpfs)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Save file to tmpfs
    file_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Update session with document info
    session_id = token_data.get("session_id")
    if session_id:
        session_data = session_manager.get_session(session_id)
        if session_data:
            document_info = {
                "document_id": doc_id,
                "filename": file.filename,
                "path": file_path,
                "size_bytes": file_size,
                "upload_time": datetime.utcnow().isoformat(),
                "file_type": file_extension
            }
            session_data["documents"].append(document_info)
    
    return DocumentInfo(
        filename=file.filename,
        size_bytes=file_size,
        size_mb=round(file_size / (1024 * 1024), 2),
        upload_time=datetime.utcnow().isoformat(),
        file_type=file_extension,
        document_id=doc_id
    )


@router.get("/list", response_model=List[DocumentInfo])
async def list_documents(token_data: Dict[str, Any] = Depends(verify_token)) -> List[DocumentInfo]:
    """List all uploaded documents for the current session"""
    
    session_id = token_data.get("session_id")
    if not session_id:
        return []
    
    session_data = session_manager.get_session(session_id)
    if not session_data:
        return []
    
    documents = []
    for doc in session_data.get("documents", []):
        documents.append(DocumentInfo(
            filename=doc["filename"],
            size_bytes=doc["size_bytes"],
            size_mb=round(doc["size_bytes"] / (1024 * 1024), 2),
            upload_time=doc["upload_time"],
            file_type=doc["file_type"],
            document_id=doc["document_id"]
        ))
    
    return documents


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    token_data: Dict[str, Any] = Depends(verify_token)
) -> Dict[str, str]:
    """Delete a document from the session"""
    
    session_id = token_data.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    session_data = session_manager.get_session(session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Find and remove document
    documents = session_data.get("documents", [])
    doc_to_remove = None
    
    for doc in documents:
        if doc["document_id"] == document_id:
            doc_to_remove = doc
            break
    
    if not doc_to_remove:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete file from tmpfs
    if os.path.exists(doc_to_remove["path"]):
        os.remove(doc_to_remove["path"])
    
    # Remove from session
    documents.remove(doc_to_remove)
    
    return {"message": f"Document {doc_to_remove['filename']} deleted successfully"}