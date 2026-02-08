#!/bin/bash
# =============================================================================
# LIST MODELS
# =============================================================================
# Lists all models currently downloaded to NVMe storage.
#
# Usage: ./maintenance/list-models.sh [--verbose]
# =============================================================================

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${SCRIPTS_DIR}/lib/logger.sh"
source "${SCRIPTS_DIR}/lib/common.sh"
source "${SCRIPTS_DIR}/config/defaults.env"

# Load AppConfig if available
if [[ -f /tmp/appconfig_cache.json ]]; then
    source "${SCRIPTS_DIR}/lib/appconfig.sh"
    MODELS_DIR=$(appconfig_get "judge_inference.storage.models_dir" "$MODELS_DIR")
fi

VERBOSE=""
[[ "${1:-}" == "--verbose" ]] && VERBOSE="1"

log_section "List Models"

log_info "Models directory: $MODELS_DIR"

# -----------------------------------------------------------------------------
# Check directory exists
# -----------------------------------------------------------------------------
if [[ ! -d "$MODELS_DIR" ]]; then
    log_warn "Models directory does not exist: $MODELS_DIR"
    exit 0
fi

# -----------------------------------------------------------------------------
# List models
# -----------------------------------------------------------------------------
log_subsection "Downloaded Models"

MODEL_COUNT=0

for model_dir in "$MODELS_DIR"/*/; do
    if [[ -d "$model_dir" ]]; then
        MODEL_NAME=$(basename "$model_dir")
        MODEL_SIZE=$(du -sh "$model_dir" 2>/dev/null | cut -f1 || echo "unknown")

        # Get model type from config.json if available
        MODEL_TYPE="unknown"
        if [[ -f "$model_dir/config.json" ]]; then
            MODEL_TYPE=$(jq -r '.model_type // "unknown"' "$model_dir/config.json" 2>/dev/null || echo "unknown")
        fi

        # Count weight files
        WEIGHT_FILES=$(find "$model_dir" -name "*.safetensors" -o -name "*.bin" 2>/dev/null | wc -l)

        echo ""
        log_success "$MODEL_NAME"
        log_info "  Size:         $MODEL_SIZE"
        log_info "  Type:         $MODEL_TYPE"
        log_info "  Weight files: $WEIGHT_FILES"
        log_info "  Path:         $model_dir"

        if [[ -n "$VERBOSE" ]] && [[ -f "$model_dir/config.json" ]]; then
            log_info "  Config:"
            jq -r 'to_entries | .[] | "    \(.key): \(.value)"' "$model_dir/config.json" 2>/dev/null | head -10 || true
        fi

        MODEL_COUNT=$((MODEL_COUNT + 1))
    fi
done

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo ""
log_subsection "Summary"

if [[ $MODEL_COUNT -eq 0 ]]; then
    log_warn "No models found in: $MODELS_DIR"
else
    TOTAL_SIZE=$(du -sh "$MODELS_DIR" 2>/dev/null | cut -f1 || echo "unknown")
    log_info "Total models: $MODEL_COUNT"
    log_info "Total size:   $TOTAL_SIZE"
fi

# Show disk space
if mountpoint -q "$(dirname "$MODELS_DIR")" 2>/dev/null || [[ -d "$MODELS_DIR" ]]; then
    DISK_INFO=$(df -h "$MODELS_DIR" 2>/dev/null | tail -1 || echo "")
    if [[ -n "$DISK_INFO" ]]; then
        DISK_USED=$(echo "$DISK_INFO" | awk '{print $3}')
        DISK_AVAIL=$(echo "$DISK_INFO" | awk '{print $4}')
        DISK_PCT=$(echo "$DISK_INFO" | awk '{print $5}')
        echo ""
        log_info "Disk usage:"
        log_info "  Used:      $DISK_USED"
        log_info "  Available: $DISK_AVAIL"
        log_info "  Percent:   $DISK_PCT"
    fi
fi
