from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any

from core.config import settings
from api import auth, documents, chat, export


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting Legal AI Sandbox - Session TTL: {settings.SESSION_TTL_HOURS} hours")
    yield
    print("Shutting down Legal AI Sandbox - Cleaning up resources")


app = FastAPI(
    title="Legal AI Research Sandbox",
    description="Secure, ephemeral environment for legal AI research",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])


@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "status": "running",
        "message": "Legal AI Research Sandbox API",
        "session_ttl_hours": settings.SESSION_TTL_HOURS,
        "max_file_size_mb": settings.MAX_FILE_SIZE_MB
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "healthy"}
