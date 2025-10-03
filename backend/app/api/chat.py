from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import httpx
import os
import logging

from app.core.config import settings
from app.core.security import verify_token, session_manager
from app.core.database import ephemeral_db
from app.core.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    document_ids: Optional[List[str]] = None
    document_contents: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    document_ids: Optional[List[str]] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    timestamp: str


class ConversationHistory(BaseModel):
    conversation_id: str
    messages: List[ChatMessage]
    created_at: str


@router.post("/send", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    token_data: Dict[str, Any] = Depends(verify_token)
) -> ChatResponse:
    """Send a message to the LLM and get a response"""

    session_id = token_data.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )

    session_data = session_manager.get_session(session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found"
        )

    # Check if Ollama is available before processing the message
    try:
        async with httpx.AsyncClient() as client:
            health_response = await client.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags",
                timeout=5.0
            )
            health_response.raise_for_status()
    except (httpx.HTTPError, httpx.TimeoutException):
        # Ollama is not available, return 503 without saving the message
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service is currently unavailable"
        )

    # Get or create conversation in database
    conversation = None
    if request.conversation_id:
        conversation = ephemeral_db.get_conversation(request.conversation_id)

    if not conversation:
        # Create new conversation
        conversation_id = f"conv_{datetime.now(timezone.utc).timestamp()}"
        conversation = ephemeral_db.create_conversation(conversation_id, session_id)
    else:
        conversation_id = conversation["conversation_id"]

    # Process documents if any are attached
    document_contents = {}
    if request.document_ids:
        session_upload_dir = os.path.join(settings.UPLOAD_DIR, session_id)

        for doc_id in request.document_ids:
            # Find the file in the upload directory
            # Look for files matching pattern: {doc_id}_{filename}
            found_file = None
            if os.path.exists(session_upload_dir):
                for filename in os.listdir(session_upload_dir):
                    if filename.startswith(f"{doc_id}_"):
                        found_file = os.path.join(session_upload_dir, filename)
                        original_filename = filename[len(doc_id) + 1:]  # Remove doc_id prefix
                        break

            if found_file and os.path.exists(found_file):
                # Process the document
                result = DocumentProcessor.extract_text(found_file)
                if not result.get("error"):
                    content = result.get("content", "")
                    # Store processed content with document metadata
                    # Use larger limit for document content (50k chars ~ 12k tokens)
                    document_contents[doc_id] = {
                        "filename": original_filename,
                        "content": DocumentProcessor.prepare_for_llm(content, max_length=50000),
                        "page_count": result.get("page_count", 0),
                        "word_count": result.get("word_count", 0)
                    }

    # Add user message to database with document associations and contents
    ephemeral_db.add_message(
        conversation_id=conversation_id,
        role="user",
        content=request.message,
        document_ids=request.document_ids,
        document_contents=document_contents
    )

    # Get full conversation history for context
    full_conversation = ephemeral_db.get_conversation(conversation_id)
    if not full_conversation:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation"
        )

    # Prepare messages for Ollama
    ollama_messages = []

    # Add conversation history with document contents inline
    for msg in full_conversation["messages"]:
        content = msg["content"]

        # If this message has document contents, include them inline with the message
        if msg.get("document_contents") and msg["role"] == "user":
            # Start with the user's message
            formatted_content = content

            # Add each document's content directly after the message
            doc_sections = []
            for doc_id, doc_data in msg["document_contents"].items():
                doc_section = f"\n\n--- Document: {doc_data['filename']} ---\n"
                doc_section += doc_data["content"]
                doc_section += f"\n--- End of {doc_data['filename']} ---"
                doc_sections.append(doc_section)

            # Combine user message with document contents
            if doc_sections:
                formatted_content = content + "\n" + "\n".join(doc_sections)

            content = formatted_content

        ollama_messages.append({
            "role": msg["role"],
            "content": content
        })

    # Call Ollama API (we already checked it's available)
    # Use longer timeout for requests with documents
    timeout_seconds = 120.0 if any(msg.get("document_contents") for msg in full_conversation["messages"]) else 60.0

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": settings.DEFAULT_MODEL,
                    "messages": ollama_messages,
                    "stream": False,
                    "options": {
                        "temperature": settings.TEMPERATURE,
                        "num_predict": settings.MAX_TOKENS
                    }
                },
                timeout=timeout_seconds
            )
            response.raise_for_status()

            result = response.json()
            assistant_response = result.get("message", {}).get("content", "")
    except httpx.TimeoutException:
        # Handle timeout specifically for large document processing
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The request took too long to process. Try with smaller documents or a simpler query."
        )
    except httpx.HTTPError as e:
        logger.error(f"Ollama API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to get response from LLM service"
        )

    # Add assistant response to database
    assistant_msg = ephemeral_db.add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_response
    )

    return ChatResponse(
        response=assistant_response,
        conversation_id=conversation_id,
        timestamp=assistant_msg["timestamp"]
    )


@router.get("/history", response_model=List[ConversationHistory])
async def get_conversation_history(
    token_data: Dict[str, Any] = Depends(verify_token)
) -> List[ConversationHistory]:
    """Get all conversation history for the current session"""

    session_id = token_data.get("session_id")
    if not session_id:
        return []

    # Get conversations from database
    db_conversations = ephemeral_db.get_conversations_for_session(session_id)

    conversations = []
    for conv in db_conversations:
        messages = [
            ChatMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["timestamp"],
                document_ids=msg.get("document_ids", []),
                document_contents=msg.get("document_contents", {})
            )
            for msg in conv["messages"]
        ]

        conversations.append(ConversationHistory(
            conversation_id=conv["conversation_id"],
            messages=messages,
            created_at=conv["created_at"]
        ))

    return conversations


@router.delete("/history/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    token_data: Dict[str, Any] = Depends(verify_token)
) -> Dict[str, str]:
    """Clear a specific conversation history"""

    session_id = token_data.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Delete from database
    deleted = ephemeral_db.delete_conversation(conversation_id, session_id)

    if deleted:
        return {"message": "Conversation cleared successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
