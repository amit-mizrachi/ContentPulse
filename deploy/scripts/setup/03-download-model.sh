#!/bin/bash
# =============================================================================
# DOWNLOAD MODEL FROM HUGGINGFACE
# =============================================================================
# Downloads a model from HuggingFace Hub to local NVMe storage.
#
# Usage: ./setup/03-download-model.sh [--model MODEL_ID] [--force]
#
# Configuration (from environment or AppConfig):
#   MODEL_ID    - HuggingFace model ID (e.g., Qwen/Qwen2.5-7B-Instruct-AWQ)
#   MODELS_DIR  - Directory to store models (default: /mnt/nvme/models)
#   HF_TOKEN    - HuggingFace API token (for gated models)
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
    MODELS_DIR=$(appconfig_get "judge_inference.storage.models_dir" "$MODELS_DIR")
fi

# Parse arguments
FORCE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL_ID="$2"
            shift 2
            ;;
        --force)
            FORCE="1"
            shift
            ;;
        *)
            die "Unknown option: $1"
            ;;
    esac
done

# Convert model ID to directory name (replace / with _)
MODEL_DIR_NAME=$(echo "$MODEL_ID" | tr '/' '_')
MODEL_PATH="${MODELS_DIR}/${MODEL_DIR_NAME}"

log_section "Download Model"

log_info "Model:      $MODEL_ID"
log_info "Target:     $MODEL_PATH"
log_info "HF Token:   ${HF_TOKEN:+<set>}${HF_TOKEN:-<not set>}"

# -----------------------------------------------------------------------------
# Check prerequisites
# -----------------------------------------------------------------------------
log_subsection "Checking Prerequisites"

# Check models directory exists and is writable
if [[ ! -d "$MODELS_DIR" ]]; then
    die "Models directory does not exist: $MODELS_DIR\nRun setup/02-mount-nvme.sh first."
fi

if [[ ! -w "$MODELS_DIR" ]]; then
    die "Models directory is not writable: $MODELS_DIR"
fi

log_success "Models directory OK: $MODELS_DIR"

# Check for Python
require_command python3 "apt-get install python3 OR brew install python3" || die "Python3 required"

# Check/install huggingface_hub
log_info "Checking huggingface_hub..."
if ! python3 -c "import huggingface_hub" &>/dev/null; then
    log_info "Installing huggingface_hub..."
    pip3 install --quiet huggingface_hub || die "Failed to install huggingface_hub"
fi
log_success "huggingface_hub available"

# -----------------------------------------------------------------------------
# Check if model already exists
# -----------------------------------------------------------------------------
log_subsection "Checking Existing Model"

if [[ -d "$MODEL_PATH" ]] && [[ "$(ls -A "$MODEL_PATH" 2>/dev/null)" ]]; then
    if [[ "$FORCE" == "1" ]]; then
        log_warn "Model exists, --force specified, removing..."
        rm -rf "$MODEL_PATH"
    else
        log_success "Model already exists at: $MODEL_PATH"

        # Show model info
        if [[ -f "$MODEL_PATH/config.json" ]]; then
            log_info "Model config:"
            jq -r '.model_type // "unknown"' "$MODEL_PATH/config.json" 2>/dev/null || true
        fi

        # Show size
        SIZE=$(du -sh "$MODEL_PATH" 2>/dev/null | cut -f1 || echo "unknown")
        log_info "Size: $SIZE"

        log_info "Use --force to re-download"
        exit 0
    fi
fi

# -----------------------------------------------------------------------------
# Download model
# -----------------------------------------------------------------------------
log_subsection "Downloading Model"

log_info "This may take several minutes for large models..."

# Create download script
DOWNLOAD_SCRIPT=$(mktemp)
cat > "$DOWNLOAD_SCRIPT" <<'PYTHON_SCRIPT'
import os
import sys
from huggingface_hub import snapshot_download

model_id = os.environ.get('MODEL_ID')
model_path = os.environ.get('MODEL_PATH')
hf_token = os.environ.get('HF_TOKEN') or os.environ.get('HUGGING_FACE_HUB_TOKEN')

if not model_id or not model_path:
    print("ERROR: MODEL_ID and MODEL_PATH must be set", file=sys.stderr)
    sys.exit(1)

print(f"Downloading {model_id} to {model_path}...")

try:
    snapshot_download(
        repo_id=model_id,
        local_dir=model_path,
        local_dir_use_symlinks=False,
        token=hf_token
    )
    print(f"Download complete: {model_path}")
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT

# Run download
export MODEL_ID MODEL_PATH HF_TOKEN
export HUGGING_FACE_HUB_TOKEN="${HF_TOKEN:-}"

START_TIME=$(date +%s)

if ! python3 "$DOWNLOAD_SCRIPT"; then
    rm -f "$DOWNLOAD_SCRIPT"
    die "Model download failed"
fi

rm -f "$DOWNLOAD_SCRIPT"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

log_success "Download completed in ${DURATION}s"

# -----------------------------------------------------------------------------
# Verify download
# -----------------------------------------------------------------------------
log_subsection "Verifying Download"

# Check essential files exist
REQUIRED_FILES=("config.json")
MISSING=()

for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$MODEL_PATH/$file" ]]; then
        MISSING+=("$file")
    fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
    log_warn "Missing expected files: ${MISSING[*]}"
else
    log_success "All expected files present"
fi

# Check for model weights
WEIGHT_FILES=$(find "$MODEL_PATH" -name "*.safetensors" -o -name "*.bin" 2>/dev/null | wc -l)
if [[ "$WEIGHT_FILES" -eq 0 ]]; then
    log_warn "No weight files found (.safetensors or .bin)"
else
    log_success "Found $WEIGHT_FILES weight file(s)"
fi

# Show final size
SIZE=$(du -sh "$MODEL_PATH" 2>/dev/null | cut -f1 || echo "unknown")
log_info "Total size: $SIZE"

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
log_subsection "Summary"

log_success "Model downloaded successfully!"
log_info "  Model ID: $MODEL_ID"
log_info "  Location: $MODEL_PATH"
log_info "  Size:     $SIZE"
log_info "  Duration: ${DURATION}s"
