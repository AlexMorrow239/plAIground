from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx

from app.core.config import settings
from app.core.security import verify_token, session_manager

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

    # Get or create conversation
    conversations = session_data.get("conversations", [])
    conversation = None

    if request.conversation_id:
        for conv in conversations:
            if conv["id"] == request.conversation_id:
                conversation = conv
                break

    if not conversation:
        # Create new conversation
        conversation = {
            "id": f"conv_{datetime.utcnow().timestamp()}",
            "messages": [],
            "created_at": datetime.utcnow().isoformat()
        }
        conversations.append(conversation)
        session_data["conversations"] = conversations

    # Add user message to history
    user_message = {
        "role": "user",
        "content": request.message,
        "timestamp": datetime.utcnow().isoformat()
    }
    conversation["messages"].append(user_message)

    # Prepare messages for Ollama
    ollama_messages = []
    for msg in conversation["messages"]:
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
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM service unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )

    # Add assistant response to history
    assistant_message = {
        "role": "assistant",
        "content": assistant_response,
        "timestamp": datetime.utcnow().isoformat()
    }
    conversation["messages"].append(assistant_message)

    return ChatResponse(
        response=assistant_response,
        conversation_id=conversation["id"],
        timestamp=assistant_message["timestamp"]
    )


@router.get("/history", response_model=List[ConversationHistory])
async def get_conversation_history(
    token_data: Dict[str, Any] = Depends(verify_token)
) -> List[ConversationHistory]:
    """Get all conversation history for the current session"""

    session_id = token_data.get("session_id")
    if not session_id:
        return []

    session_data = session_manager.get_session(session_id)
    if not session_data:
        return []

    conversations = []
    for conv in session_data.get("conversations", []):
        messages = [
            ChatMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["timestamp"]
            )
            for msg in conv["messages"]
        ]

        conversations.append(ConversationHistory(
            conversation_id=conv["id"],
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

    session_data = session_manager.get_session(session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    conversations = session_data.get("conversations", [])
    conv_to_remove = None

    for conv in conversations:
        if conv["id"] == conversation_id:
            conv_to_remove = conv
            break

    if conv_to_remove:
        conversations.remove(conv_to_remove)
        return {"message": "Conversation cleared successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
