#!/bin/bash
# =============================================================================
# FETCH CONFIGURATION
# =============================================================================
# Fetches configuration from AWS AppConfig and exports as environment variables.
# Falls back to defaults.env if AppConfig is not available.
#
# Usage:
#   ./fetch-config.sh              # Fetch and display config
#   source <(./fetch-config.sh)    # Fetch and export to current shell
#   eval $(./fetch-config.sh)      # Alternative export method
#
# Required Environment Variables:
#   APPCONFIG_APPLICATION_ID  - AppConfig application ID
#   APPCONFIG_ENVIRONMENT_ID  - AppConfig environment ID
#   APPCONFIG_PROFILE_ID      - AppConfig configuration profile ID
#   AWS_REGION                - AWS region
# =============================================================================

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPTS_DIR}/lib/logger.sh"
source "${SCRIPTS_DIR}/lib/common.sh"

# Check if we should output export statements (for sourcing)
OUTPUT_EXPORTS=""
if [[ "${1:-}" == "--export" ]] || [[ ! -t 1 ]]; then
    OUTPUT_EXPORTS="1"
fi

log_section "Fetch Configuration"

# -----------------------------------------------------------------------------
# Load defaults first
# -----------------------------------------------------------------------------
log_subsection "Loading Defaults"

if [[ -f "${SCRIPTS_DIR}/config/defaults.env" ]]; then
    source "${SCRIPTS_DIR}/config/defaults.env"
    log_success "Loaded defaults from: config/defaults.env"
else
    log_warn "No defaults.env found"
fi

# -----------------------------------------------------------------------------
# Try AppConfig
# -----------------------------------------------------------------------------
log_subsection "Fetching from AppConfig"

APPCONFIG_SUCCESS=""

if [[ -n "${APPCONFIG_APPLICATION_ID:-}" ]] && \
   [[ -n "${APPCONFIG_ENVIRONMENT_ID:-}" ]] && \
   [[ -n "${APPCONFIG_PROFILE_ID:-}" ]]; then

    log_info "AppConfig IDs configured, attempting fetch..."

    source "${SCRIPTS_DIR}/lib/appconfig.sh"

    if appconfig_fetch; then
        APPCONFIG_SUCCESS="1"
        log_success "AppConfig fetch successful"

        # Export values from AppConfig
        appconfig_export_env "judge_inference"
    else
        log_warn "AppConfig fetch failed, using defaults"
    fi
else
    log_info "AppConfig not configured, using defaults"
    log_debug "Set APPCONFIG_APPLICATION_ID, APPCONFIG_ENVIRONMENT_ID, and APPCONFIG_PROFILE_ID to enable"
fi

# -----------------------------------------------------------------------------
# Display/Export configuration
# -----------------------------------------------------------------------------
log_subsection "Configuration Values"

# Define all config keys we care about
declare -A CONFIG_VARS=(
    ["MODEL_ID"]="${MODEL_ID:-}"
    ["MODEL_QUANTIZATION"]="${MODEL_QUANTIZATION:-}"
    ["MODEL_MAX_LEN"]="${MODEL_MAX_LEN:-}"
    ["MODEL_GPU_MEMORY_UTILIZATION"]="${MODEL_GPU_MEMORY_UTILIZATION:-}"
    ["NVME_DEVICE"]="${NVME_DEVICE:-}"
    ["NVME_MOUNT_PATH"]="${NVME_MOUNT_PATH:-}"
    ["MODELS_DIR"]="${MODELS_DIR:-}"
    ["VLLM_IMAGE"]="${VLLM_IMAGE:-}"
    ["VLLM_TAG"]="${VLLM_TAG:-}"
    ["VLLM_PORT"]="${VLLM_PORT:-}"
    ["VLLM_HOST"]="${VLLM_HOST:-}"
    ["K8S_NAMESPACE"]="${K8S_NAMESPACE:-}"
    ["K8S_SERVICE_NAME"]="${K8S_SERVICE_NAME:-}"
    ["K8S_HF_SECRET_NAME"]="${K8S_HF_SECRET_NAME:-}"
    ["AWS_REGION"]="${AWS_REGION:-}"
)

# Output configuration
for key in "${!CONFIG_VARS[@]}"; do
    value="${CONFIG_VARS[$key]}"
    if [[ -n "$OUTPUT_EXPORTS" ]]; then
        echo "export $key=\"$value\""
    else
        log_info "$key=$value"
    fi
done

# Also export AppConfig IDs if set
if [[ -n "${APPCONFIG_APPLICATION_ID:-}" ]]; then
    if [[ -n "$OUTPUT_EXPORTS" ]]; then
        echo "export APPCONFIG_APPLICATION_ID=\"$APPCONFIG_APPLICATION_ID\""
        echo "export APPCONFIG_ENVIRONMENT_ID=\"$APPCONFIG_ENVIRONMENT_ID\""
        echo "export APPCONFIG_PROFILE_ID=\"$APPCONFIG_PROFILE_ID\""
    fi
fi

# -----------------------------------------------------------------------------
# Save to file for other scripts
# -----------------------------------------------------------------------------
CONFIG_ENV_FILE="/tmp/judge_inference_config.env"

{
    echo "# Judge Inference Configuration"
    echo "# Generated at: $(date)"
    echo "# Source: ${APPCONFIG_SUCCESS:+AppConfig}${APPCONFIG_SUCCESS:-defaults.env}"
    echo ""
    for key in "${!CONFIG_VARS[@]}"; do
        echo "export $key=\"${CONFIG_VARS[$key]}\""
    done
} > "$CONFIG_ENV_FILE"

if [[ -z "$OUTPUT_EXPORTS" ]]; then
    log_success "Configuration saved to: $CONFIG_ENV_FILE"
    log_info "Source with: source $CONFIG_ENV_FILE"
fi
