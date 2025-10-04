# Development Setup - Legal AI Research Sandbox

## Overview

Setup instructions for working with the implemented authentication system and placeholder components.

## Prerequisites

- Python 3.11+
- Node.js 18+ or Bun
- Docker/Podman (for containerized development)
- Git

## Local Development Setup

### 1. Backend Setup (Authentication Working)

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install uv package manager
pip install uv

# Install dependencies
uv sync

# Copy environment template
cp .env.example .env.local

# Generate test sessions for authentication
cd ..
python deployment/scripts/provision_session.py

# This creates: deployment/sessions/local/sessions.json
# Displays credentials like:
# Username: researcher_a1b2c3d4
# Password: xK9$mP2@vQ7!nR8#
# Session ID: Abc123...
```

**Start the backend server:**

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

**Verify backend is running:**

- Visit: <http://localhost:8000>
- Should show: `{"status": "running", "message": "Legal AI Research Sandbox API", ...}`
- Health check: <http://localhost:8000/health>

### 2. Frontend Setup (Authentication Working)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
bun install  # or npm install

# Copy environment template
cp .env.example .env.local

# Start development server
bun dev  # or npm run dev
```

**Verify frontend is running:**

- Visit: <http://localhost:3000>
- Should redirect to login page at <http://localhost:3000/login>

### 3. Test Authentication Flow

1. **Access the application**: Navigate to <http://localhost:3000>
2. **Login page**: You'll be redirected to the login form
3. **Use generated credentials**: Enter the username/password from the provision script output
4. **Successful login**: Should redirect to dashboard at <http://localhost:3000/dashboard>
5. **Protected routes**: Try accessing /documents or /chat - should work with authentication
6. **Logout**: Clear browser storage or restart - should redirect back to login

### 4. Verify Session Management

**Check session loading in backend logs:**

```
Starting Legal AI Sandbox - Session TTL: 72 hours
Loading sessions from: deployment/sessions/local/sessions.json
Loaded 1 active session(s)
```

**Test invalid credentials:**

- Try wrong username/password - should show error message
- Check network tab for proper 401 responses

## Container Development Setup

### 1. Build Container Images

```bash
# Build both services
docker-compose build

# Verify images are created
docker images | grep legal
```

### 2. Provision Container Session

```bash
# Create an isolated session container
python deployment/scripts/provision_session.py --container

# Example output:
# CONTAINER MODE: Creating 1 isolated container session(s)
# Base port: 8100
# ✓ Generated session 1/1: Ab12Cd34Ef56
# 🐳 Starting container for session Ab12Cd34Ef56
#    Backend:  http://localhost:8200
#    Frontend: http://localhost:8201
# ✓ Container started successfully
# ✓ Backend health check passed
```

### 3. Access Container Session

- **Frontend**: <http://localhost:[assigned_port>] (e.g., 8201)
- **Backend API**: <http://localhost:[assigned_port-1>] (e.g., 8200)
- **Credentials**: Use the displayed username/password from provision output

### 4. Container Management

**List active containers:**

```bash
python deployment/scripts/list_active_sessions.py
```

**Stop specific session:**

```bash
docker-compose --env-file deployment/sessions/[session_id]/.env down
```

**Cleanup all sessions:**

```bash
python deployment/scripts/cleanup_session_containers.py --all
```

## Development Workflow

### Working with Authentication

- Authentication is fully functional for development
- Sessions persist in browser storage
- Token expires after 72 hours (matches session TTL)
- Backend automatically loads sessions from JSON file on startup

### Working with Placeholder Features

- Document upload/management pages exist but have no backend integration
- Chat interface exists but no LLM connection
- Export buttons exist but don't perform actual exports
- All placeholder pages are accessible with valid authentication

### Adding New Features

1. **Backend**: Implement actual business logic in existing API endpoints
2. **Frontend**: Connect UI components to backend APIs using existing React Query setup
3. **Testing**: Use authentication flow as reference for proper integration

### Environment Variables

**Backend (.env.local):**

```env
SECRET_KEY=your-secret-key-here
SESSION_TTL_HOURS=72
ALLOWED_ORIGINS=http://localhost:3000
OLLAMA_BASE_URL=http://localhost:11434  # For future LLM integration
DEFAULT_MODEL=deepseek-r1:8b                # For future LLM integration
```

**Frontend (.env.local):**

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Troubleshooting

### Backend Issues

- **"No sessions.json found"**: Run `python deployment/scripts/provision_session.py`
- **"Port already in use"**: Change port in uvicorn command or kill existing process
- **"Module not found"**: Ensure you're in backend directory and virtual environment is activated

### Frontend Issues

- **"API connection failed"**: Verify backend is running on port 8000
- **"Login not working"**: Check credentials match those from provision script
- **"Redirect loop"**: Clear browser storage and cookies

### Container Issues

- **"Port already in use"**: Use `--base-port` flag with different port
- **"Container startup failed"**: Check Docker daemon is running
- **"Health check failed"**: Wait a few seconds for services to fully start

## File Structure Reference

```txt
plAIground/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API endpoints (auth working, others placeholder)
│   │   ├── core/              # Configuration and security (working)
│   │   └── main.py            # Application entry point (working)
│   ├── .env.example           # Environment template
│   └── sessions.json          # Generated by provision script
├── frontend/                   # Next.js frontend
│   ├── app/                   # Pages (login working, others placeholder UI)
│   ├── components/            # UI components
│   ├── lib/                   # API client and utilities (working)
│   └── .env.example           # Environment template
├── deployment/
│   ├── scripts/               # Session provisioning and management
│   └── sessions/              # Generated session data
└── docker-compose.yml         # Container orchestration
```

This setup provides a working authentication foundation for continuing development of the remaining features.
