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

- **Framework**: FastAPI 0.116.1+
  - Chosen for async support and automatic OpenAPI documentation
  - Built-in WebSocket support for streaming responses
  - Type hints and Pydantic integration

### LLM Serving Layer

**Option 2: Ollama (Easier deployment)**

```bash
ollama/ollama:0.1.29
# Models: llama3:8b, mistral:7b, mixtral:8x7b
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
- **Package Manager**: bun

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

### State Management

```json
{
  "zustand": "^4.4.0", // Lightweight state management
  "react-query": "^3.39.0" // Server state management
}
```

### Code & Text Editing

```json
{
  "@monaco-editor/react": "^4.6.0", // VS Code editor
  "react-markdown": "^9.0.0", // Markdown rendering
  "react-syntax-highlighter": "^15.5.0"
}
```

### Real-time Communication

```json
{
  "socket.io-client": "^4.6.0", // WebSocket client
  "axios": "^1.6.0", // HTTP client
  "swr": "^2.2.0" // Data fetching with caching
}
```

### File Handling

```json
{
  "react-dropzone": "^14.2.0", // Drag-n-drop uploads
  "file-saver": "^2.0.5", // File downloads
  "jszip": "^3.10.0" // ZIP file creation
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
  "vitest": "^1.1.0" // Testing framework
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

## Model Configuration for MVP

### Single Model Setup

```yaml
# Llama-3-8B with Ollama (Recommended for MVP)
model:
  name: "llama3:8b"
  memory_required: "16GB"
```
