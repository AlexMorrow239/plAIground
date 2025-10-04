#!/bin/bash
set -e

# Ollama Initialization Script
# Automatically pulls and serves the model specified by DEFAULT_MODEL
# Supports multiple models via OLLAMA_MODELS (comma-separated)

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_MODEL="${DEFAULT_MODEL:-deepseek-r1:8b}"
OLLAMA_MODELS="${OLLAMA_MODELS:-$DEFAULT_MODEL}"
MAX_RETRIES=30
RETRY_DELAY=1

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Start Ollama server
log_info "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
log_info "Waiting for Ollama server to be ready..."
RETRIES=0
while [ $RETRIES -lt $MAX_RETRIES ]; do
    # Use ollama list command to check if server is ready
    if ollama list >/dev/null 2>&1; then
        log_success "Ollama server is ready!"
        break
    fi
    RETRIES=$((RETRIES + 1))
    if [ $RETRIES -eq $MAX_RETRIES ]; then
        log_error "Ollama server failed to start after $MAX_RETRIES attempts"
        exit 1
    fi
    sleep $RETRY_DELAY
done

# Function to pull a model
pull_model() {
    local model=$1
    log_info "Checking if model '$model' exists..."

    # Check if model already exists
    if ollama list 2>/dev/null | grep -q "^${model}"; then
        log_success "Model '$model' already exists"
        return 0
    fi

    log_info "Pulling model '$model'..."

    # Pull the model with progress output
    if ollama pull "$model"; then
        log_success "Model '$model' pulled successfully"

        # Verify model is available
        if ollama list 2>/dev/null | grep -q "^${model}"; then
            log_success "Model '$model' verified and ready to use"
            return 0
        else
            log_warning "Model '$model' was pulled but not found in list"
            return 1
        fi
    else
        log_error "Failed to pull model '$model'"
        return 1
    fi
}

# Parse and pull models
IFS=',' read -ra MODELS <<< "$OLLAMA_MODELS"
FAILED_MODELS=()

log_info "Models to pull: ${MODELS[*]}"

for model in "${MODELS[@]}"; do
    # Trim whitespace
    model=$(echo "$model" | xargs)

    if [ -n "$model" ]; then
        if ! pull_model "$model"; then
            FAILED_MODELS+=("$model")
        fi
    fi
done

# Report status
if [ ${#FAILED_MODELS[@]} -eq 0 ]; then
    log_success "All models ready!"
    log_info "Available models:"
    ollama list
else
    log_warning "Some models failed to pull: ${FAILED_MODELS[*]}"
    log_info "Available models:"
    ollama list
fi

# Keep the container running
log_info "Ollama server is running with PID $OLLAMA_PID"
log_info "Default model: $DEFAULT_MODEL"

# Wait for Ollama server process
wait $OLLAMA_PID
