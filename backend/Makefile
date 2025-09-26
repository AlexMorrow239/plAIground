# Legal AI Research Sandbox - Backend Makefile

# Default target
.DEFAULT_GOAL := help

# Variables
VENV_ACTIVATE := source .venv/bin/activate &&
PYTHON := $(VENV_ACTIVATE) python3
UVICORN := $(VENV_ACTIVATE) uvicorn
APP_MODULE := app.main:app
HOST := 127.0.0.1
PORT := 8000

# Help target
help:
	@echo "Legal AI Research Sandbox - Backend"
	@echo "Available commands:"
	@echo "  dev     - Run development server with hot reload"
	@echo "  run     - Run production server"
	@echo "  install - Install dependencies with uv"
	@echo "  clean   - Clean up temporary files"
	@echo "  help    - Show this help message"

# Development server with hot reload
dev:
	@echo "Starting development server..."
	$(UVICORN) $(APP_MODULE) --host $(HOST) --port $(PORT) --reload --app-dir .

# Production server
run:
	@echo "Starting production server..."
	$(UVICORN) $(APP_MODULE) --host $(HOST) --port $(PORT) --app-dir .

# Install dependencies
install:
	@echo "Installing dependencies..."
	uv sync

# Clean temporary files
clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -f sessions.json
	rm -rf /tmp/sandbox/

# Run with custom host/port
run-custom:
	@echo "Starting server on $(HOST):$(PORT)..."
	$(UVICORN) $(APP_MODULE) --host $(HOST) --port $(PORT) --app-dir .

.PHONY: help dev run install clean run-custom
