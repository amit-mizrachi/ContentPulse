#!/bin/bash
# =============================================================================
# UPDATE MODEL
# =============================================================================
# Downloads a new version of a model and performs an atomic swap.
# Keeps the old version as a backup until the new version is verified.
#
# Usage: ./maintenance/update-model.sh [--model MODEL_ID] [--no-backup]
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

NO_BACKUP=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL_ID="$2"
            shift 2
            ;;
        --no-backup)
            NO_BACKUP="1"
            shift
            ;;
        *)
            die "Unknown option: $1"
            ;;
    esac
done

MODEL_DIR_NAME=$(echo "$MODEL_ID" | tr '/' '_')
MODEL_PATH="${MODELS_DIR}/${MODEL_DIR_NAME}"
MODEL_PATH_NEW="${MODEL_PATH}.new"
MODEL_PATH_BACKUP="${MODEL_PATH}.backup"

log_section "Update Model"

log_info "Model ID:      $MODEL_ID"
log_info "Current path:  $MODEL_PATH"
log_info "Temp path:     $MODEL_PATH_NEW"
log_info "Backup path:   $MODEL_PATH_BACKUP"

# -----------------------------------------------------------------------------
# Check current model exists
# -----------------------------------------------------------------------------
log_subsection "Checking Current Model"

if [[ ! -d "$MODEL_PATH" ]]; then
    log_warn "Current model not found, performing fresh download instead"
    exec "${SCRIPTS_DIR}/setup/03-download-model.sh" --model "$MODEL_ID"
fi

CURRENT_SIZE=$(du -sh "$MODEL_PATH" 2>/dev/null | cut -f1 || echo "unknown")
log_info "Current model size: $CURRENT_SIZE"

# -----------------------------------------------------------------------------
# Download new version
# -----------------------------------------------------------------------------
log_subsection "Downloading New Version"

# Clean up any previous failed update
rm -rf "$MODEL_PATH_NEW"

log_info "Downloading to temporary location..."

# Use the download script but redirect to .new path
MODELS_DIR_ORIG="$MODELS_DIR"
export MODELS_DIR="${MODELS_DIR}/.tmp_update"
mkdir -p "$MODELS_DIR"

"${SCRIPTS_DIR}/setup/03-download-model.sh" --model "$MODEL_ID" --force

# Move from temp location to .new
mv "${MODELS_DIR}/${MODEL_DIR_NAME}" "$MODEL_PATH_NEW"
rmdir "$MODELS_DIR" 2>/dev/null || true
export MODELS_DIR="$MODELS_DIR_ORIG"

NEW_SIZE=$(du -sh "$MODEL_PATH_NEW" 2>/dev/null | cut -f1 || echo "unknown")
log_success "New version downloaded: $NEW_SIZE"

# -----------------------------------------------------------------------------
# Verify new version
# -----------------------------------------------------------------------------
log_subsection "Verifying New Version"

ERRORS=()

# Check config.json
if [[ ! -f "$MODEL_PATH_NEW/config.json" ]]; then
    ERRORS+=("Missing config.json")
fi

# Check for weight files
WEIGHT_COUNT=$(find "$MODEL_PATH_NEW" -name "*.safetensors" -o -name "*.bin" 2>/dev/null | wc -l)
if [[ "$WEIGHT_COUNT" -eq 0 ]]; then
    ERRORS+=("No weight files found")
fi

if [[ ${#ERRORS[@]} -gt 0 ]]; then
    log_error "New version verification failed:"
    for err in "${ERRORS[@]}"; do
        log_error "  - $err"
    done
    log_info "Cleaning up failed download..."
    rm -rf "$MODEL_PATH_NEW"
    die "Update aborted"
fi

log_success "New version verified"

# -----------------------------------------------------------------------------
# Atomic swap
# -----------------------------------------------------------------------------
log_subsection "Performing Atomic Swap"

# Backup current version
if [[ -z "$NO_BACKUP" ]]; then
    log_info "Backing up current version..."
    rm -rf "$MODEL_PATH_BACKUP"
    mv "$MODEL_PATH" "$MODEL_PATH_BACKUP"
    log_success "Backup created: $MODEL_PATH_BACKUP"
else
    log_info "Removing current version (no backup)..."
    rm -rf "$MODEL_PATH"
fi

# Move new version into place
log_info "Installing new version..."
mv "$MODEL_PATH_NEW" "$MODEL_PATH"
log_success "New version installed"

# -----------------------------------------------------------------------------
# Cleanup backup (optional)
# -----------------------------------------------------------------------------
if [[ -z "$NO_BACKUP" ]] && [[ -d "$MODEL_PATH_BACKUP" ]]; then
    log_subsection "Cleanup"

    BACKUP_SIZE=$(du -sh "$MODEL_PATH_BACKUP" 2>/dev/null | cut -f1 || echo "unknown")
    log_info "Backup size: $BACKUP_SIZE"

    if confirm "Delete backup to reclaim space?" "y"; then
        rm -rf "$MODEL_PATH_BACKUP"
        log_success "Backup deleted"
    else
        log_info "Backup kept at: $MODEL_PATH_BACKUP"
        log_info "Delete manually with: rm -rf $MODEL_PATH_BACKUP"
    fi
fi

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
log_subsection "Summary"

log_success "Model update complete!"
log_info "  Model:     $MODEL_ID"
log_info "  Location:  $MODEL_PATH"
log_info "  Old size:  $CURRENT_SIZE"
log_info "  New size:  $NEW_SIZE"

if [[ -d "$MODEL_PATH_BACKUP" ]]; then
    log_info "  Backup:    $MODEL_PATH_BACKUP"
fi

log_info ""
log_warn "Remember to restart the vLLM service to load the new model!"
