from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import httpx

from app.core.config import settings
from app.core.security import verify_token, session_manager
from app.core.database import ephemeral_db

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


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

    # Add user message to database
    ephemeral_db.add_message(
        conversation_id=conversation_id,
        role="user",
        content=request.message
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
    for msg in full_conversation["messages"]:
        ollama_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Call Ollama API
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
                timeout=30.0
            )
            response.raise_for_status()

            result = response.json()
            assistant_response = result.get("message", {}).get("content", "")

    except httpx.HTTPError as e:
        # For now, use a mock response when Ollama is not available
        assistant_response = f"I understand you said: '{request.message}'. The LLM service is currently unavailable, but your message has been saved."
    except Exception as e:
        assistant_response = f"I received your message: '{request.message}'. There was an error processing it, but it has been saved."

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
                timestamp=msg["timestamp"]
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
