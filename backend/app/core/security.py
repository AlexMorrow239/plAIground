from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import string

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def generate_session_credentials() -> Dict[str, str]:
    """Generate unique session credentials for manual provisioning"""
    username = f"researcher_{secrets.token_hex(4)}"
    password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
    password_hash = get_password_hash(password)
    
    return {
        "username": username,
        "password": password,
        "password_hash": password_hash
    }


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token from request"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


class SessionManager:
    """Manage in-memory session data"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_start_times: Dict[str, datetime] = {}
    
    def create_session(self, username: str, password_hash: str) -> str:
        """Create a new session"""
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = {
            "username": username,
            "password_hash": password_hash,
            "created_at": datetime.utcnow(),
            "documents": [],
            "conversations": [],
            "active": True
        }
        self.session_start_times[session_id] = datetime.utcnow()
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Update session data"""
        if session_id in self.sessions:
            self.sessions[session_id].update(data)
    
    def delete_session(self, session_id: str) -> None:
        """Delete session and all associated data"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.session_start_times:
            del self.session_start_times[session_id]
    
    def get_session_time_remaining(self, session_id: str) -> Optional[timedelta]:
        """Calculate remaining time for session"""
        if session_id not in self.session_start_times:
            return None
        
        start_time = self.session_start_times[session_id]
        elapsed = datetime.utcnow() - start_time
        total_allowed = timedelta(hours=settings.SESSION_TTL_HOURS)
        remaining = total_allowed - elapsed
        
        return remaining if remaining.total_seconds() > 0 else timedelta(0)
    
    def cleanup_expired_sessions(self) -> None:
        """Remove expired sessions"""
        current_time = datetime.utcnow()
        expired_sessions = []
        
        for session_id, start_time in self.session_start_times.items():
            if (current_time - start_time) > timedelta(hours=settings.SESSION_TTL_HOURS):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.delete_session(session_id)


session_manager = SessionManager()