#!/bin/bash
# =============================================================================
# START vLLM SERVER
# =============================================================================
# Starts the vLLM inference server with configuration from AppConfig.
# This script is typically used as the container entrypoint.
#
# Usage: ./runtime/start-vllm.sh
#
# Configuration (from environment or AppConfig):
#   MODEL_PATH                  - Path to model on disk
#   MODEL_QUANTIZATION          - Quantization type (awq, gptq, etc.)
#   MODEL_MAX_LEN               - Maximum context length
#   MODEL_GPU_MEMORY_UTILIZATION - GPU memory fraction to use
#   VLLM_PORT                   - Port to serve on
#   VLLM_HOST                   - Host to bind to
# =============================================================================

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${SCRIPTS_DIR}/lib/logger.sh"
source "${SCRIPTS_DIR}/lib/common.sh"
source "${SCRIPTS_DIR}/config/defaults.env"

# Load AppConfig if available
if [[ -f /tmp/appconfig_cache.json ]]; then
    source "${SCRIPTS_DIR}/lib/appconfig.sh"
    MODEL_ID=$(appconfig_get "judge_inference.model.id" "$MODEL_ID")
    MODEL_QUANTIZATION=$(appconfig_get "judge_inference.model.quantization" "$MODEL_QUANTIZATION")
    MODEL_MAX_LEN=$(appconfig_get "judge_inference.model.max_model_len" "$MODEL_MAX_LEN")
    MODEL_GPU_MEMORY_UTILIZATION=$(appconfig_get "judge_inference.model.gpu_memory_utilization" "$MODEL_GPU_MEMORY_UTILIZATION")
    MODELS_DIR=$(appconfig_get "judge_inference.storage.models_dir" "$MODELS_DIR")
    VLLM_PORT=$(appconfig_get "judge_inference.vllm.port" "$VLLM_PORT")
fi

# Derive model path if not explicitly set
MODEL_DIR_NAME=$(echo "$MODEL_ID" | tr '/' '_')
MODEL_PATH="${MODEL_PATH:-${MODELS_DIR}/${MODEL_DIR_NAME}}"

log_section "Start vLLM Server"

log_info "Model path:   $MODEL_PATH"
log_info "Quantization: $MODEL_QUANTIZATION"
log_info "Max length:   $MODEL_MAX_LEN"
log_info "GPU memory:   $MODEL_GPU_MEMORY_UTILIZATION"
log_info "Port:         $VLLM_PORT"

# -----------------------------------------------------------------------------
# Validate model exists
# -----------------------------------------------------------------------------
log_subsection "Validating Model"

if [[ ! -d "$MODEL_PATH" ]]; then
    die "Model directory not found: $MODEL_PATH"
fi

if [[ ! -f "$MODEL_PATH/config.json" ]]; then
    die "Model config.json not found in: $MODEL_PATH"
fi

log_success "Model found: $MODEL_PATH"

# -----------------------------------------------------------------------------
# Build vLLM arguments
# -----------------------------------------------------------------------------
log_subsection "Building Arguments"

VLLM_ARGS=(
    "--model" "$MODEL_PATH"
    "--port" "$VLLM_PORT"
    "--host" "${VLLM_HOST:-0.0.0.0}"
)

# Add quantization if specified
if [[ -n "$MODEL_QUANTIZATION" ]] && [[ "$MODEL_QUANTIZATION" != "none" ]]; then
    VLLM_ARGS+=("--quantization" "$MODEL_QUANTIZATION")
fi

# Add max model length
if [[ -n "$MODEL_MAX_LEN" ]]; then
    VLLM_ARGS+=("--max-model-len" "$MODEL_MAX_LEN")
fi

# Add GPU memory utilization
if [[ -n "$MODEL_GPU_MEMORY_UTILIZATION" ]]; then
    VLLM_ARGS+=("--gpu-memory-utilization" "$MODEL_GPU_MEMORY_UTILIZATION")
fi

# Add dtype
VLLM_ARGS+=("--dtype" "half")

# Enable trust remote code (needed for some models)
VLLM_ARGS+=("--trust-remote-code")

log_info "vLLM arguments: ${VLLM_ARGS[*]}"

# -----------------------------------------------------------------------------
# Check for GPU
# -----------------------------------------------------------------------------
log_subsection "Checking GPU"

if command -v nvidia-smi &>/dev/null; then
    if nvidia-smi &>/dev/null; then
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
        GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader | head -1)
        log_success "GPU available: $GPU_NAME ($GPU_MEM)"
    else
        die "nvidia-smi failed - GPU not accessible"
    fi
else
    log_warn "nvidia-smi not found - assuming GPU is available"
fi

# -----------------------------------------------------------------------------
# Start vLLM
# -----------------------------------------------------------------------------
log_subsection "Starting vLLM"

log_info "Starting vLLM server..."
log_info "Endpoint will be available at: http://${VLLM_HOST:-0.0.0.0}:${VLLM_PORT}/v1"

# Check if python/vllm is available
if command -v python3 &>/dev/null; then
    # Check if vllm module is available
    if python3 -c "import vllm" &>/dev/null; then
        log_info "Using vLLM Python module"
        exec python3 -m vllm.entrypoints.openai.api_server "${VLLM_ARGS[@]}"
    fi
fi

# Try vllm command directly (if installed as CLI)
if command -v vllm &>/dev/null; then
    log_info "Using vLLM CLI"
    exec vllm serve "${VLLM_ARGS[@]}"
fi

die "vLLM not found. Install with: pip install vllm"
