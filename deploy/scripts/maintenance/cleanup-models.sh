#!/bin/bash
# =============================================================================
# CLEANUP MODELS
# =============================================================================
# Removes old or unused models from NVMe storage.
#
# Usage: ./maintenance/cleanup-models.sh [--keep MODEL_ID] [--dry-run] [--force]
#
# Options:
#   --keep MODEL_ID   Keep this model (can be specified multiple times)
#   --dry-run         Show what would be deleted without deleting
#   --force           Skip confirmation prompt
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
    CURRENT_MODEL=$(appconfig_get "judge_inference.model.id" "$MODEL_ID")
fi

# Default: keep currently configured model
CURRENT_MODEL_DIR=$(echo "${CURRENT_MODEL:-$MODEL_ID}" | tr '/' '_')
KEEP_MODELS=("$CURRENT_MODEL_DIR")

DRY_RUN=""
FORCE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --keep)
            KEEP_MODELS+=("$(echo "$2" | tr '/' '_')")
            shift 2
            ;;
        --dry-run)
            DRY_RUN="1"
            shift
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

log_section "Cleanup Models"

log_info "Models directory: $MODELS_DIR"
log_info "Models to keep:"
for model in "${KEEP_MODELS[@]}"; do
    log_info "  - $model"
done
[[ -n "$DRY_RUN" ]] && log_warn "DRY RUN MODE - no files will be deleted"

# -----------------------------------------------------------------------------
# Check directory exists
# -----------------------------------------------------------------------------
if [[ ! -d "$MODELS_DIR" ]]; then
    log_warn "Models directory does not exist: $MODELS_DIR"
    exit 0
fi

# -----------------------------------------------------------------------------
# Find models to delete
# -----------------------------------------------------------------------------
log_subsection "Scanning Models"

TO_DELETE=()
TOTAL_SIZE=0

for model_dir in "$MODELS_DIR"/*/; do
    if [[ -d "$model_dir" ]]; then
        MODEL_NAME=$(basename "$model_dir")

        # Check if in keep list
        KEEP=""
        for keep_model in "${KEEP_MODELS[@]}"; do
            if [[ "$MODEL_NAME" == "$keep_model" ]]; then
                KEEP="1"
                break
            fi
        done

        if [[ -n "$KEEP" ]]; then
            log_info "KEEP: $MODEL_NAME"
        else
            SIZE=$(du -sb "$model_dir" 2>/dev/null | cut -f1 || echo "0")
            SIZE_HUMAN=$(du -sh "$model_dir" 2>/dev/null | cut -f1 || echo "unknown")
            log_warn "DELETE: $MODEL_NAME ($SIZE_HUMAN)"
            TO_DELETE+=("$model_dir")
            TOTAL_SIZE=$((TOTAL_SIZE + SIZE))
        fi
    fi
done

# -----------------------------------------------------------------------------
# Summary and confirm
# -----------------------------------------------------------------------------
if [[ ${#TO_DELETE[@]} -eq 0 ]]; then
    log_success "No models to clean up"
    exit 0
fi

echo ""
log_subsection "Summary"

TOTAL_SIZE_HUMAN=$(numfmt --to=iec-i --suffix=B "$TOTAL_SIZE" 2>/dev/null || echo "${TOTAL_SIZE} bytes")
log_warn "Models to delete: ${#TO_DELETE[@]}"
log_warn "Space to recover: $TOTAL_SIZE_HUMAN"

if [[ -n "$DRY_RUN" ]]; then
    log_info ""
    log_info "Dry run complete. Use without --dry-run to actually delete."
    exit 0
fi

# Confirm deletion
if [[ -z "$FORCE" ]]; then
    echo ""
    if ! confirm "Delete ${#TO_DELETE[@]} model(s) and recover $TOTAL_SIZE_HUMAN?" "n"; then
        log_info "Aborted"
        exit 0
    fi
fi

# -----------------------------------------------------------------------------
# Delete models
# -----------------------------------------------------------------------------
log_subsection "Deleting Models"

DELETED=0
FAILED=0

for model_dir in "${TO_DELETE[@]}"; do
    MODEL_NAME=$(basename "$model_dir")
    log_info "Deleting: $MODEL_NAME"

    if rm -rf "$model_dir"; then
        log_success "Deleted: $MODEL_NAME"
        DELETED=$((DELETED + 1))
    else
        log_error "Failed to delete: $MODEL_NAME"
        FAILED=$((FAILED + 1))
    fi
done

# -----------------------------------------------------------------------------
# Final summary
# -----------------------------------------------------------------------------
echo ""
log_subsection "Results"

log_success "Deleted: $DELETED model(s)"
if [[ $FAILED -gt 0 ]]; then
    log_error "Failed:  $FAILED model(s)"
fi
log_info "Space recovered: $TOTAL_SIZE_HUMAN"

# Show remaining disk space
if [[ -d "$MODELS_DIR" ]]; then
    DISK_AVAIL=$(df -h "$MODELS_DIR" 2>/dev/null | tail -1 | awk '{print $4}')
    log_info "Available space: $DISK_AVAIL"
fi
