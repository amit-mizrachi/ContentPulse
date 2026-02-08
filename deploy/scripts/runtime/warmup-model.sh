#!/bin/bash
# =============================================================================
# WARMUP MODEL
# =============================================================================
# Sends a warmup request to the vLLM server to preload the model into GPU memory.
# This reduces latency for the first real request.
#
# Usage: ./runtime/warmup-model.sh [--host HOST] [--port PORT]
# =============================================================================

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${SCRIPTS_DIR}/lib/logger.sh"
source "${SCRIPTS_DIR}/lib/common.sh"
source "${SCRIPTS_DIR}/config/defaults.env"

# Load AppConfig if available
if [[ -f /tmp/appconfig_cache.json ]]; then
    source "${SCRIPTS_DIR}/lib/appconfig.sh"
    VLLM_PORT=$(appconfig_get "judge_inference.vllm.port" "$VLLM_PORT")
fi

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            VLLM_HOST="$2"
            shift 2
            ;;
        --port)
            VLLM_PORT="$2"
            shift 2
            ;;
        *)
            die "Unknown option: $1"
            ;;
    esac
done

VLLM_HOST="${VLLM_HOST:-localhost}"
BASE_URL="http://${VLLM_HOST}:${VLLM_PORT}"

log_section "Warmup Model"

log_info "Target: $BASE_URL"

# -----------------------------------------------------------------------------
# Wait for server to be ready
# -----------------------------------------------------------------------------
log_subsection "Waiting for Server"

MAX_WAIT=300
WAIT_INTERVAL=5

log_info "Waiting for vLLM server to be ready (max ${MAX_WAIT}s)..."

ELAPSED=0
while [[ $ELAPSED -lt $MAX_WAIT ]]; do
    if curl -s "${BASE_URL}/health" &>/dev/null; then
        log_success "Server is ready!"
        break
    fi

    sleep $WAIT_INTERVAL
    ELAPSED=$((ELAPSED + WAIT_INTERVAL))
    log_debug "Waiting... ($ELAPSED/${MAX_WAIT}s)"
done

if [[ $ELAPSED -ge $MAX_WAIT ]]; then
    die "Timeout waiting for server to be ready"
fi

# -----------------------------------------------------------------------------
# Get model name
# -----------------------------------------------------------------------------
log_subsection "Getting Model Info"

MODELS_RESPONSE=$(curl -s "${BASE_URL}/v1/models")
MODEL_NAME=$(echo "$MODELS_RESPONSE" | jq -r '.data[0].id // empty' 2>/dev/null)

if [[ -z "$MODEL_NAME" ]]; then
    die "Could not determine model name from /v1/models response"
fi

log_info "Model: $MODEL_NAME"

# -----------------------------------------------------------------------------
# Send warmup request
# -----------------------------------------------------------------------------
log_subsection "Sending Warmup Request"

WARMUP_PROMPT="Hello, this is a warmup request to preload the model."

log_info "Sending warmup inference request..."

START_TIME=$(date +%s.%N)

RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d "{
        \"model\": \"$MODEL_NAME\",
        \"messages\": [
            {\"role\": \"user\", \"content\": \"$WARMUP_PROMPT\"}
        ],
        \"max_tokens\": 10,
        \"temperature\": 0
    }" 2>&1)

END_TIME=$(date +%s.%N)
DURATION=$(echo "$END_TIME - $START_TIME" | bc 2>/dev/null || echo "?")

# Check response
if echo "$RESPONSE" | jq -e '.choices[0].message.content' &>/dev/null; then
    CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content')
    log_success "Warmup request completed in ${DURATION}s"
    log_debug "Response: $CONTENT"
else
    ERROR=$(echo "$RESPONSE" | jq -r '.error.message // .detail // "Unknown error"' 2>/dev/null || echo "$RESPONSE")
    log_warn "Warmup request may have failed: $ERROR"
fi

# -----------------------------------------------------------------------------
# Verify model is hot
# -----------------------------------------------------------------------------
log_subsection "Verifying Model State"

# Send a second quick request to verify
START_TIME=$(date +%s.%N)

RESPONSE2=$(curl -s -X POST "${BASE_URL}/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d "{
        \"model\": \"$MODEL_NAME\",
        \"messages\": [
            {\"role\": \"user\", \"content\": \"Hi\"}
        ],
        \"max_tokens\": 5,
        \"temperature\": 0
    }" 2>&1)

END_TIME=$(date +%s.%N)
DURATION2=$(echo "$END_TIME - $START_TIME" | bc 2>/dev/null || echo "?")

log_success "Second request completed in ${DURATION2}s"

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
log_subsection "Summary"

log_success "Model warmup complete!"
log_info "  Model:           $MODEL_NAME"
log_info "  First request:   ${DURATION}s"
log_info "  Second request:  ${DURATION2}s"
log_info "  Endpoint:        ${BASE_URL}/v1/chat/completions"
