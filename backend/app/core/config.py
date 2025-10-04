from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env.local file
load_dotenv('.env.local')


class Settings(BaseSettings):
    PROJECT_NAME: str = "Legal AI Research Sandbox"
    VERSION: str = "1.0.0"

    # Container Configuration
    SESSION_ID: Optional[str] = os.getenv("SESSION_ID")
    IS_CONTAINERIZED: bool = os.getenv("SESSION_ID") is not None

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production-use-secrets-module")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Session Management
    SESSION_TTL_HOURS: int = int(os.getenv("SESSION_TTL_HOURS", "72"))
    SESSION_WARNING_MINUTES: List[int] = [60, 15, 5]  # Warning times before expiration

    # CORS - Allow any localhost/127.0.0.1 on any port
    ALLOWED_ORIGINS: str = os.getenv(
        "ALLOWED_ORIGINS",
        r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    )

    # File Upload - Container-aware paths
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", 100))
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".txt", ".docx"]

    @property
    def UPLOAD_DIR(self) -> str:
        """Dynamic upload directory based on environment."""
        base_dir = os.getenv("UPLOAD_DIR", "/tmp/sandbox/uploads")

        # Ensure directory exists in container
        if self.IS_CONTAINERIZED:
            os.makedirs(base_dir, exist_ok=True)

        return base_dir

    # LLM Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "llama3:8b")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4096"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))

    # Developer Tools - Optional session file override for local development
    LOCAL_SESSIONS_FILE: Optional[str] = os.getenv("LOCAL_SESSIONS_FILE")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
