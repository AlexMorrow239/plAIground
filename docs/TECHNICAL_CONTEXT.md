# Technical Context - Legal AI Research Sandbox

## Architecture Overview

The Legal AI Research Sandbox is designed as a secure, ephemeral environment for legal researchers to interact with LLMs using confidential documents. The system emphasizes complete data isolation and automatic cleanup.

## Current Implementation Architecture

### Authentication-First Design

The system is built with **authentication as the foundation**, with all other features as placeholder implementations that integrate into the existing auth framework.

```txt
┌─────────────────┐    JWT Token    ┌─────────────────┐
│   Frontend      │◄──────────────►│   Backend       │
│   (Next.js)     │   API Calls     │   (FastAPI)     │
│                 │                 │                 │
│ ✅ Auth Pages   │                 │ ✅ JWT Auth     │
│ 📝 Placeholder │                 │ 📝 Placeholder │
│    UI Pages     │                 │    API Endpoints│
└─────────────────┘                 └─────────────────┘
        │                                     │
        │                                     │
        ▼                                     ▼
┌─────────────────┐                 ┌─────────────────┐
│ Container       │                 │ Session Storage │
│ Isolation       │                 │ (In-Memory)     │
│ ✅ Working      │                 │ ✅ Working      │
└─────────────────┘                 └─────────────────┘
```

## Working Components

### 1. Authentication System ✅

**Backend (`app/core/security.py`):**

- JWT token generation with 72-hour expiration
- bcrypt password hashing and verification
- Session management with automatic TTL cleanup
- In-memory session storage loaded from sessions.json

**Frontend (`lib/auth-context.tsx`):**

- React Context for global auth state
- Token storage in browser localStorage
- Automatic token inclusion in API requests
- Protected route middleware in Next.js

**Integration Points:**

- Login: `POST /api/auth/login` with username/password
- Token verification: `Authorization: Bearer {token}` header
- Session data: JWT payload contains `session_id` and `sub` (username)

### 2. Container Isolation System ✅

**Per-Session Containers:**

- Unique Docker network per session (`{session_id}_network`)
- Isolated port allocation (auto-assigned from base port)
- Tmpfs-only storage (`/tmp/sandbox` with 10GB limit)
- Resource limits (32GB RAM, 4 CPU cores max)

**Session Provisioning:**

```python
# Creates isolated container with:
python deployment/scripts/provision_session.py --container

# Results in:
# - Unique session credentials
# - Isolated Docker network
# - Ephemeral file storage
# - Automatic TTL enforcement
```

### 3. Environment Detection ✅

**Backend Configuration (`app/core/config.py`):**

- Detects container vs local environment via `SESSION_ID` env var
- Dynamic CORS origins based on deployment mode
- Container-aware file paths and directory creation
- Automatic resource path configuration

**Frontend Configuration (`lib/env.ts`):**

- API URL configuration for container vs local development
- Environment-specific build settings

## Placeholder Integration Points

### 1. Document Management 📝

**Expected Flow (Not Yet Implemented):**

```
Frontend Upload → Backend /api/documents/upload → Tmpfs Storage
                                ↓
                  Extract Text (pypdf/python-docx)
                                ↓
                  Store in Session Memory
```

**Current State:**

- API endpoints exist but not tested
- File validation logic present but not integrated
- Tmpfs paths configured but no actual file handling

### 2. LLM Integration 📝

**Expected Flow (Not Yet Implemented):**

```
Frontend Chat → Backend /api/chat/send → Ollama Service
                            ↓
               Context + Documents → LLM Response
                            ↓
               Store in Conversation History
```

**Current State:**

- Chat API structure exists
- Ollama service defined in docker-compose
- No actual LLM service connection or testing

### 3. Export System 📝

**Expected Flow (Not Yet Implemented):**

```
Frontend Export → Backend /api/export/download → Session Data
                                ↓
                  JSON File Generation → File Download
```

**Current State:**

- Export endpoints exist with data structure
- Session aggregation logic present but not tested
- File download headers configured but not verified

## Critical Dependencies & Integration Points

### Sessions.json File

**Required for backend startup:**

```json
{
  "generated_at": "2025-01-09T...",
  "sessions": [
    {
      "session_id": "...",
      "username": "researcher_...",
      "password_hash": "$2b$12$...",
      "created_at": "2025-01-09T...",
      "expires_at": "2025-01-12T...",
      "documents": [],
      "conversations": []
    }
  ]
}
```

### API Client Integration

**Frontend (`lib/api.ts`):**

```typescript
// All API calls use this centralized client
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    Authorization: `Bearer ${token}`, // Auto-added for auth
  },
});
```

### Docker Network Configuration

**Per-session isolation:**

```yaml
networks:
  session_network:
    name: ${SESSION_ID}_network
    ipam:
      config:
        - subnet: ${SESSION_SUBNET} # Unique per session
```

## Security Architecture

### Data Ephemeral Storage

- **Tmpfs mounts**: All data stored in RAM, not disk
- **Container lifecycle**: Data destroyed when container stops
- **No persistence**: No databases, no file system writes outside tmpfs

### Network Isolation

- **Bridge networks**: Each session gets isolated network
- **No external access**: Containers cannot reach internet
- **Port isolation**: Each session gets unique host ports

### Session Security

- **Time-limited**: 72-hour TTL with automatic cleanup
- **Credential isolation**: Each session has unique username/password
- **JWT expiration**: Tokens expire with session TTL

## Development Integration Points

### Adding New Features

1. **Follow auth pattern**: Use `verify_token` dependency in backend endpoints
2. **Use React Query**: Frontend API integration follows existing pattern
3. **Session storage**: Add data to session object in memory
4. **Container awareness**: Use environment detection for paths/URLs

### Testing New Features

1. **Authentication first**: Ensure login works before testing other features
2. **Use existing sessions**: Generate via provision script for consistent testing
3. **Container testing**: Test both local and containerized modes
4. **Session cleanup**: Verify TTL and cleanup behavior

### Known Limitations

- **No persistent storage**: All data lost on container restart
- **In-memory only**: No database, limited to container memory
- **Single-container**: No horizontal scaling or load balancing
- **Manual provisioning**: No self-service user registration

## Future Integration Requirements

### For Document Features

- Install text extraction libraries: `pypdf`, `python-docx`, `pdfplumber`
- Implement text processing in document upload endpoints
- Add document viewing/search capabilities

### For LLM Features

- Set up Ollama service with model loading
- Implement RAG pipeline with document context
- Add streaming response capability

### For Export Features

- Test actual file generation and download
- Verify session data completeness
- Add export format options

This architecture provides a solid foundation with working authentication and container isolation, ready for feature implementation using the established patterns.
