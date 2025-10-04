# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development - Full Stack

```bash
# Start both frontend and backend concurrently
# Terminal 1 - Backend (FastAPI on port 8000)
cd backend && make dev

# Terminal 2 - Frontend (Next.js on port 3000)
cd frontend && bun dev

# Docker Compose - Run entire stack
docker-compose up --build
```

### Backend Commands

```bash
cd backend
make install         # Install Python dependencies with uv
make dev             # Run with hot reload (port 8000)
make run             # Production server
make clean           # Clean temp files
uv run pyright       # Type checking
uv run black app/    # Format code
uv run isort app/    # Sort imports
```

### Frontend Commands

```bash
cd frontend
bun dev              # Development with Turbopack (port 3000)
bun run build        # Production build
bun start            # Production server
bun lint             # Run ESLint
```

### Session Management

```bash
# Generate test session (from project root)
python deployment/scripts/provision_session.py

# Manage Docker containers
python deployment/scripts/manage_session_containers.py
python deployment/scripts/cleanup_session_containers.py
```

## Architecture - System Overview

This is a secure, ephemeral Legal AI Research Sandbox where researchers interact with LLMs using confidential documents. The system ensures complete data isolation and destruction after use.

### Core Design Principles

- **Zero Data Persistence**: All data stored in RAM (tmpfs), destroyed on container termination
- **Session Isolation**: Each user gets isolated Docker container with unique network
- **72-Hour Duration**: Sessions expire after 72 hours with automatic cleanup
- **JWT Authentication**: Stateless auth with session-scoped tokens

### Service Communication

```
User Browser → Frontend (Next.js:3000) → Backend (FastAPI:8000) → Ollama (future)
                    ↓                           ↓
              localStorage (JWT)         In-Memory Storage
                                         sessions.json (read-only)
```

### Authentication Flow

1. Frontend sends credentials to `/api/auth/login`
2. Backend validates against `sessions.json`
3. Returns JWT token with session expiry time
4. Frontend stores token in localStorage
5. All API calls include `Authorization: Bearer <token>`
6. Backend validates token and extracts session_id

### Session Lifecycle

1. **Provisioning**: Admin runs `provision_session.py` → creates session in `sessions.json`
2. **Container Start**: Docker Compose spins up isolated environment
3. **User Access**: Login with provided credentials
4. **Usage**: Upload docs, interact with LLM (when implemented)
5. **Auto-Cleanup**: Background task removes expired sessions every 5 min
6. **Termination**: Container destroyed, all data erased

### API Structure

**Working Endpoints**:

- `POST /api/auth/login` - JWT authentication
- `POST /api/auth/logout` - Token invalidation
- `GET /api/auth/status` - Session info & TTL

**Placeholder Endpoints** (return mock data):

- `/api/documents/*` - Document management
- `/api/chat/*` - LLM interaction
- `/api/export/*` - Data export

### Environment Variables

**Backend** (`backend/.env`):

```bash
SECRET_KEY=your-secret-key-here
SESSION_ID=unique-session-id        # Set by Docker
OLLAMA_BASE_URL=http://ollama:11434 # For future LLM integration
```

**Frontend** (`frontend/.env.local`):

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MAX_FILE_SIZE_MB=100
NEXT_PUBLIC_ALLOWED_FILE_TYPES=.pdf,.txt,.docx
```

### Docker Network Architecture

Each session gets isolated network:

- Frontend container: `<session_id>_frontend`
- Backend container: `<session_id>_backend`
- Network: `<session_id>_network` (172.20.0.0/24)
- Ollama container: `<session_id>_ollama` (when enabled)

### File Storage Paths

**Container Mode** (production):

- Sessions: `/app/sessions.json` (read-only mount)
- Uploads: `/tmp/sandbox/uploads/{session_id}/`
- Documents: `/tmp/sandbox/documents/{session_id}/`

**Local Mode** (development):

- Sessions: `../deployment/sessions/local/sessions.json`
- Uploads: `./temp/uploads/{session_id}/`
- Documents: `./temp/documents/{session_id}/`

### Protected Route Pattern

**Backend** (FastAPI):

```python
from app.core.security import verify_token
from fastapi import Depends

@router.get("/protected")
async def route(token_data: Dict = Depends(verify_token)):
    session_id = token_data.get("session_id")
    # Session-scoped operations
```

**Frontend** (Next.js):

```tsx
// Use ProtectedRoute component
import ProtectedRoute from "@/components/ProtectedRoute";

// API calls automatically include auth
const { data } = useQuery({
  queryKey: ["documents"],
  queryFn: () => apiClient.getDocuments(), // Token injected
});
```

### State Management

**Frontend**:

- Auth state: React Context (`AuthProvider`)
- Server state: React Query (1-min cache)
- Local state: Component useState

**Backend**:

- Session data: In-memory dict synced to JSON
- File storage: tmpfs (RAM-based)
- No database or persistent storage

### Security Features

- JWT tokens expire with session
- bcrypt password hashing
- CORS configured for local ports only
- No data persistence after container stops
- Network isolation per session
- Resource limits (32GB RAM, 4 CPUs)

### Testing Authentication

```bash
# 1. Generate session
python deployment/scripts/provision_session.py

# 2. Note credentials (e.g., researcher_abc123 / test_password)

# 3. Start services
cd backend && make dev  # Terminal 1
cd frontend && bun dev  # Terminal 2

# 4. Login at http://localhost:3000

# 5. Test API directly
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "researcher_abc123", "password": "test_password"}'
```

## Implementation Status

### ✅ Fully Implemented

- JWT authentication system
- Session management with TTL
- Protected routes (frontend & backend)
- Docker containerization
- CORS configuration
- Session countdown timer

### 📝 Placeholder/Mock

- Document upload processing
- Text extraction from PDFs/DOCX
- LLM integration (Ollama)
- Chat interface functionality
- Export functionality

### 🚧 TODO for Production

```bash
# Add document processing libraries
cd backend
uv add pypdf python-docx pdfplumber

# Pull Ollama models (in container)
docker exec -it <session_id>_ollama ollama pull deepseek-r1:8b
```

## Development Tips

1. **Check Container Mode**: Look for `SESSION_ID` env var
2. **Session File Format**: See `backend/CLAUDE.md` for structure
3. **Frontend Dev Tools**: React Query DevTools available in dev mode
4. **API Docs**: <http://localhost:8000/docs> (FastAPI Swagger)
5. **Hot Reload**: Both frontend (Turbopack) and backend (uvicorn --reload) support it

## Common Tasks

### Add New Protected API Endpoint

1. Create route in `backend/app/api/`
2. Use `Depends(verify_token)` for auth
3. Add types to `frontend/types/index.ts`
4. Add API method to `frontend/lib/api.ts`
5. Create React Query hook in `frontend/lib/hooks.ts`

### Deploy New Session

1. Run `provision_session.py` with desired parameters
2. Set environment variables (SESSION_ID, ports)
3. Run `docker-compose up -d`
4. Share credentials with researcher

### Debug Authentication Issues

1. Check browser DevTools for token in localStorage
2. Verify `/api/auth/status` returns session info
3. Check backend logs for JWT validation errors
4. Ensure `sessions.json` contains user entry
