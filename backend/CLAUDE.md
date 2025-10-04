# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
```bash
# Install dependencies
make install

# Run development server with hot reload
make dev                    # Runs on port 8000

# Run production server
make run                    # No auto-reload

# Clean temporary files
make clean                  # Removes __pycache__, *.pyc, sessions.json

# Custom host/port
HOST=0.0.0.0 PORT=9000 make run-custom

# Type checking
uv run pyright

# Format code (line length 88)
uv run black app/
uv run isort app/
```

### Testing API Endpoints
```bash
# View API documentation
open http://localhost:8000/docs

# Test authentication (requires session from provision_session.py)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "researcher_abc123", "password": "test_password"}'
```

## Architecture

This is a FastAPI backend for the plAIground Legal AI Research Sandbox - a secure, ephemeral environment for legal researchers to interact with LLMs using confidential documents.

### Core Principles
- **Session Isolation**: Each user session runs in an isolated container with its own network
- **Ephemeral Storage**: All data stored in tmpfs (RAM), destroyed on container termination
- **Auto-cleanup**: Sessions expire after 72 hours with automatic cleanup every 5 minutes
- **No Database**: All session data stored in-memory and synced to JSON file

### Key Components

1. **Authentication (`app/core/security.py`, `app/api/auth.py`)**: JWT-based auth with bcrypt password hashing. Sessions loaded from `sessions.json` file.

2. **Configuration (`app/core/config.py`)**: Environment-aware settings that detect container vs local mode via `SESSION_ID` env var.

3. **Session Management**: In-memory storage with TTL tracking. Background task removes expired sessions.

4. **API Structure**:
   - `/api/auth/*` - Authentication endpoints (✅ working)
   - `/api/documents/*` - Document upload/management (📝 placeholder)
   - `/api/chat/*` - LLM chat interface (📝 placeholder)
   - `/api/export/*` - Data export (📝 placeholder)

### Important Patterns

**Protected Routes**: Use FastAPI dependency injection
```python
from app.core.security import verify_token
from fastapi import Depends

@router.get("/protected")
async def route(token_data: Dict = Depends(verify_token)):
    session_id = token_data.get("session_id")
```

**Session-Scoped Storage**: All file operations must be scoped to session
```python
session_dir = os.path.join(settings.UPLOAD_DIR, session_id)
os.makedirs(session_dir, exist_ok=True)
```

**Environment Detection**: Check if running in container
```python
IS_CONTAINERIZED = os.getenv("SESSION_ID") is not None
```

### File Locations

- **Container Mode**:
  - Sessions: `/app/sessions.json`
  - Uploads: `/tmp/sandbox/uploads/{session_id}/`
  - Documents: `/tmp/sandbox/documents/{session_id}/`

- **Local Mode**:
  - Sessions: `../deployment/sessions/local/sessions.json`
  - Uploads: `./temp/uploads/{session_id}/`
  - Documents: `./temp/documents/{session_id}/`

### Missing Dependencies for Full Functionality

To enable document processing and text extraction:
```bash
uv add pypdf python-docx pdfplumber
```

### Session File Format
Sessions are stored in JSON with this structure:
```json
{
  "sessions": [
    {
      "session_id": "unique_id",
      "username": "researcher_abc123",
      "password_hash": "$2b$12$...",
      "expires_at": "2025-01-12T12:00:00Z",
      "documents": [],
      "conversations": []
    }
  ]
}
```

### Development Tips

1. **Generate Test Sessions**: Run `python ../deployment/scripts/provision_session.py` from project root
2. **Check Container Mode**: Look for `SESSION_ID` environment variable
3. **Session Duration**: Default 72 hours, sessions expire based on `expires_at` timestamp
4. **File Size Limit**: 100MB default, configurable via `MAX_FILE_SIZE_MB`
5. **Allowed Files**: `.pdf`, `.txt`, `.docx` only