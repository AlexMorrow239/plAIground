from pydantic_settings import BaseSettings
from typing import List
import os
from datetime import timedelta


class Settings(BaseSettings):
    PROJECT_NAME: str = "Legal AI Research Sandbox"
    VERSION: str = "1.0.0"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production-use-secrets-module")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 72  # 72 hours to match session TTL
    
    # Session Management
    SESSION_TTL_HOURS: int = 72
    SESSION_WARNING_MINUTES: List[int] = [60, 15, 5]  # Warning times before expiration
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    
    # File Upload
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".txt", ".docx"]
    UPLOAD_DIR: str = "/tmp/sandbox/uploads"  # tmpfs mount point
    
    # LLM Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    DEFAULT_MODEL: str = "llama3:8b"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.7
    
    # Database (in-memory only for MVP)
    USE_IN_MEMORY_STORAGE: bool = True
    
    # Admin Credentials (for manual provisioning)
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD_HASH: str = os.getenv("ADMIN_PASSWORD_HASH", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()