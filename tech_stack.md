# Technical Stack Specification
## Legal AI Research Sandbox

### Overview
This document details the complete technical stack for the Legal AI Research Sandbox, a secure, ephemeral environment for conducting AI research with confidential legal documents.

---

## Core Infrastructure

### Container Runtime
- **Technology**: Podman 4.x
- **Mode**: Rootless containers for enhanced security
- **Orchestration**: Podman-compose for multi-container coordination
- **Registry**: Local registry for storing base images

### Host Environment
- **Platform**: University HPC Cluster (Linux-based)
- **OS**: RHEL 8.x / Rocky Linux 8.x / Ubuntu 22.04 LTS
- **Runtime**: Python 3.11+ environment
- **Resource Manager**: SLURM/PBS (cluster integration)

---

## Backend Stack

### Primary Framework
- **Framework**: FastAPI 0.104+
  - Chosen for async support and automatic OpenAPI documentation
  - Built-in WebSocket support for streaming responses
  - Type hints and Pydantic integration

### API Components
```python
fastapi==0.104.0
uvicorn[standard]==0.24.0  # ASGI server
python-multipart==0.0.6    # File upload support
python-jose[cryptography]  # JWT tokens
passlib[bcrypt]==1.7.4    # Password hashing
```

### LLM Serving Layer
**Option 1: vLLM (Recommended for performance)**
```python
vllm==0.2.7
ray==2.9.0  # Distributed inference
```

**Option 2: Ollama (Easier deployment)**
```bash
ollama/ollama:0.1.29
# Models: llama3:8b, mistral:7b, mixtral:8x7b
```

**Option 3: llama-cpp-python (Lightweight)**
```python
llama-cpp-python==0.2.55
# CPU-optimized inference
```

### Document Processing
```python
# Text extraction
pypdf==3.17.0           # PDF processing
python-docx==1.1.0      # DOCX processing
pdfplumber==0.10.3      # Complex PDF extraction
pypandoc==1.12          # Universal document converter

# NLP & Embeddings
langchain==0.1.0        # Document chunking, RAG pipeline
sentence-transformers==2.3.0  # Document embeddings
chromadb==0.4.22        # In-memory vector store
tiktoken==0.5.2         # Token counting
```

### Async Task Processing
```python
celery==5.3.4
redis==5.0.1  # In-memory only, no persistence
flower==2.0.1  # Task monitoring (dev only)
```

### Data Validation & Serialization
```python
pydantic==2.5.0
pydantic-settings==2.1.0
marshmallow==3.20.0  # Alternative serialization
```

### Security & Authentication
```python
# Core security
cryptography==41.0.7
secrets  # Built-in secure random generation
hashlib  # Built-in hashing

# Session management
pytz==2023.3
python-dateutil==2.8.2
```

---

## Frontend Stack

### Core Framework
- **Framework**: React 18.2.0
- **Language**: TypeScript 5.3
- **Build Tool**: Vite 5.0 (faster than CRA)
- **Package Manager**: pnpm (efficient dependency management)

### UI Component Library
**Option 1: Material-UI (MUI)**
```json
{
  "@mui/material": "^5.15.0",
  "@mui/icons-material": "^5.15.0",
  "@emotion/react": "^11.11.0",
  "@emotion/styled": "^11.11.0"
}
```

**Option 2: Ant Design**
```json
{
  "antd": "^5.12.0",
  "@ant-design/icons": "^5.2.0"
}
```

### State Management
```json
{
  "zustand": "^4.4.0",      // Lightweight state management
  "react-query": "^3.39.0", // Server state management
  "immer": "^10.0.0"        // Immutable state updates
}
```

### Code & Text Editing
```json
{
  "@monaco-editor/react": "^4.6.0",  // VS Code editor
  "react-markdown": "^9.0.0",        // Markdown rendering
  "react-syntax-highlighter": "^15.5.0"
}
```

### Real-time Communication
```json
{
  "socket.io-client": "^4.6.0",     // WebSocket client
  "axios": "^1.6.0",                 // HTTP client
  "swr": "^2.2.0"                    // Data fetching with caching
}
```

### File Handling
```json
{
  "react-dropzone": "^14.2.0",      // Drag-n-drop uploads
  "file-saver": "^2.0.5",           // File downloads
  "jszip": "^3.10.0"                // ZIP file creation
}
```

### Development Tools
```json
{
  "@types/react": "^18.2.0",
  "@types/node": "^20.10.0",
  "@typescript-eslint/eslint-plugin": "^6.15.0",
  "@typescript-eslint/parser": "^6.15.0",
  "prettier": "^3.1.0",
  "eslint": "^8.56.0",
  "vitest": "^1.1.0"  // Testing framework
}
```

---

## Database & Storage

### Session Storage (Ephemeral)
- **Technology**: Redis 7.2 (in-memory only)
- **Configuration**: No persistence, no AOF, no RDB
- **Usage**: Session tokens, rate limiting, temporary caches

### Vector Database (In-memory)
- **Technology**: ChromaDB or Qdrant
- **Mode**: Ephemeral collections
- **Usage**: Document embeddings for RAG

### File Storage
- **Location**: Container's `/tmp` directory
- **Mount**: `tmpfs` for RAM-based storage
- **Cleanup**: Automatic on container termination

---

## Infrastructure as Code

### Container Definition
```dockerfile
# Base image
FROM python:3.11-slim-bookworm

# Security hardening
RUN useradd -m -s /bin/bash sandboxuser
USER sandboxuser

# No persistent volumes
VOLUME ["/tmp/sandbox"]
```

### Deployment Tools
```yaml
# docker-compose.yml structure
version: '3.9'
services:
  api:
    build: ./backend
    tmpfs:
      - /tmp:size=10G
  
  frontend:
    build: ./frontend
    depends_on:
      - api
  
  redis:
    image: redis:7.2-alpine
    command: redis-server --save "" --appendonly no
```

---

## Development Tools

### Version Control
- **Git**: 2.40+
- **Pre-commit hooks**: black, isort, flake8, mypy
- **Commit convention**: Conventional Commits

### Testing Frameworks
**Backend Testing**
```python
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-cov==4.1.0
httpx==0.25.0  # Async test client
faker==20.0.0  # Test data generation
```

**Frontend Testing**
```json
{
  "vitest": "^1.1.0",
  "@testing-library/react": "^14.1.0",
  "@testing-library/jest-dom": "^6.1.0",
  "msw": "^2.0.0"  // API mocking
}
```

### CI/CD Pipeline
- **GitHub Actions** or **GitLab CI**
- **Container Registry**: Harbor or GitLab Registry
- **Security Scanning**: Trivy, Snyk

---

## Monitoring & Logging

### Application Monitoring
```python
# Structured logging
structlog==23.2.0
python-json-logger==2.0.7

# Metrics (optional for MVP)
prometheus-client==0.19.0
```

### Container Monitoring
- **cAdvisor**: Container metrics
- **Grafana**: Visualization (optional)
- **Loki**: Log aggregation (optional)

---

## Security Tools

### Dependency Scanning
```bash
# Python
safety==3.0.0
bandit==1.7.5

# JavaScript
npm audit
snyk
```

### Runtime Security
- **AppArmor/SELinux**: Mandatory access controls
- **Seccomp**: System call filtering
- **Capabilities**: Dropped unnecessary Linux capabilities

---

## Model Configuration for MVP

### Single Model Setup (Choose One)
```yaml
# Llama-3-8B with Ollama (Recommended for MVP)
model:
  name: "llama3:8b"
  memory_required: "16GB"
  
# OR Mistral-7B (Lighter alternative)
model:
  name: "mistral:7b" 
  memory_required: "14GB"
```

## Minimum Requirements for MVP

### Software Versions
- Python: 3.11+
- Podman: 4.0+
- Ollama: Latest (if using Ollama)

### Hardware Requirements (Per Container)
- RAM: 32GB minimum (16GB for model + overhead)
- CPU: 8 cores minimum
- Storage: 10GB tmpfs

### OS Requirements
- RHEL 8+ / Ubuntu 22.04 / Rocky Linux 8+
- Podman installed and configured
- Basic firewall allowing port 8000

## Phase 2 Enhancements (After MVP)

Once MVP is working, consider adding:

### Enhanced Backend
- Redis for session management
- LangChain for better RAG
- WebSockets for streaming
- Better error handling

### Improved Frontend  
- React for better UI
- Real-time updates
- Progress indicators
- Responsive design

### Additional Features
- Multiple model support
- Document search
- Advanced export options
- Monitoring dashboard

### Security Hardening
- TLS/HTTPS
- Rate limiting
- Input sanitization
- Audit logging

## Implementation Timeline

### Week 1: Core Backend
- Basic FastAPI setup
- Simple authentication
- File upload/storage
- LLM integration (Ollama)

### Week 2: Frontend & Integration
- Basic HTML interface
- Chat functionality
- Export feature
- Container configuration
- Testing & documentation

### Week 3-4: Enhancements (If Time Permits)
- Add P1 requirements
- Improve UI
- Add monitoring
- Security hardening

## Key Decisions for MVP

1. **LLM Serving**: Use Ollama for simplicity
2. **Frontend**: Start with plain HTML/JS
3. **Storage**: Python dictionaries (no Redis initially)
4. **Auth**: Environment variables for credentials
5. **Deployment**: Manual bash scripts

These choices prioritize getting a working system quickly while maintaining the core security requirements of ephemeral storage and container isolation.