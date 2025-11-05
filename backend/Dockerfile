# Legal AI Research Sandbox Backend Container
# Multi-stage build for security and optimization

FROM docker.io/library/python:3.12-slim-bullseye AS base

# Security: Create non-root user
RUN groupadd --gid 1000 sandbox && \
    useradd --uid 1000 --gid sandbox --shell /bin/bash --create-home sandbox

# Install system dependencies and security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up Python environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create application directory with proper permissions
WORKDIR /app
RUN chown sandbox:sandbox /app

# Create tmpfs mount points for ephemeral storage
RUN mkdir -p /tmp/sandbox/uploads /tmp/sandbox/documents /tmp/sandbox/sessions && \
    chown -R sandbox:sandbox /tmp/sandbox && \
    chmod 755 /tmp/sandbox && \
    chmod 755 /tmp/sandbox/uploads /tmp/sandbox/documents /tmp/sandbox/sessions

# Install uv for fast package management
RUN pip install uv

# Copy dependency files
COPY --chown=sandbox:sandbox pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY --chown=sandbox:sandbox . .

# Switch to non-root user
USER sandbox

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set resource limits and security constraints
ENV MAX_MEMORY=32 \
    MAX_TMPFS=10 \
    UPLOAD_DIR=/tmp/sandbox/uploads

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
