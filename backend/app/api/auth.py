from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.config import settings
from app.core.security import (
    verify_password,
    create_access_token,
    verify_token,
    session_manager
)

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    session_id: str
    expires_at: str


class SessionInfo(BaseModel):
    username: str
    time_remaining_hours: float
    time_remaining_minutes: int
    session_active: bool


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest) -> LoginResponse:
    """
    Manual login with provided credentials.
    Credentials are provisioned by admin and sent via secure channel.
    """
    print(f"Login attempt for user: {credentials.username}")
    print(f"Active sessions: {list(session_manager.sessions.keys())}")
    # Check if user exists in active sessions
    session_data = None
    session_id = ""

    for sid, data in session_manager.sessions.items():
        if data["username"] == credentials.username:
            session_data = data
            session_id = sid
            break

    if not session_data or not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please use the credentials provided by your administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(credentials.password, session_data["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please use the credentials provided by your administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": credentials.username, "session_id": session_id},
        expires_delta=access_token_expires
    )

    # Get session expires_at
    expires_at = session_data.get('expires_at')
    if isinstance(expires_at, datetime):
        expires_at_str = expires_at.isoformat()
    else:
        expires_at_str = str(expires_at) if expires_at else ""

    return LoginResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        session_id=session_id,
        expires_at=expires_at_str
    )


@router.get("/session", response_model=SessionInfo)
async def get_session_info(token_data: Dict[str, Any] = Depends(verify_token)) -> SessionInfo:
    """Get current session information including time remaining"""

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

    time_remaining = session_manager.get_session_time_remaining(session_id)
    if not time_remaining:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )

    total_minutes = int(time_remaining.total_seconds() / 60)
    hours = total_minutes / 60

    return SessionInfo(
        username=session_data["username"],
        time_remaining_hours=round(hours, 2),
        time_remaining_minutes=total_minutes,
        session_active=session_data.get("active", True)
    )


@router.post("/logout")
async def logout(token_data: Dict[str, Any] = Depends(verify_token)) -> Dict[str, str]:
    """
    Logout doesn't delete the session (that happens on TTL expiry).
    It just marks the session as logged out.
    """
    session_id = token_data.get("session_id")
    if session_id:
        session_data = session_manager.get_session(session_id)
        if session_data:
            session_data["active"] = False

    return {"message": "Logged out successfully"}
