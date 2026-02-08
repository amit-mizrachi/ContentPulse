#!/bin/bash
# =============================================================================
# VALIDATE SETUP
# =============================================================================
# Verifies that all components are properly configured and ready.
# Collects all errors and reports at the end.
#
# Usage: ./setup/05-validate-setup.sh [--verbose]
# =============================================================================

set -uo pipefail  # Note: not using -e, we collect all errors

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${SCRIPTS_DIR}/lib/logger.sh"
source "${SCRIPTS_DIR}/lib/common.sh"
source "${SCRIPTS_DIR}/config/defaults.env"

# Load AppConfig if available
if [[ -f /tmp/appconfig_cache.json ]]; then
    source "${SCRIPTS_DIR}/lib/appconfig.sh"
    MODEL_ID=$(appconfig_get "judge_inference.model.id" "$MODEL_ID")
    NVME_MOUNT_PATH=$(appconfig_get "judge_inference.storage.nvme_mount_path" "$NVME_MOUNT_PATH")
    MODELS_DIR=$(appconfig_get "judge_inference.storage.models_dir" "$MODELS_DIR")
    K8S_NAMESPACE=$(appconfig_get "judge_inference.kubernetes.namespace" "$K8S_NAMESPACE")
    K8S_HF_SECRET_NAME=$(appconfig_get "judge_inference.kubernetes.hf_secret_name" "$K8S_HF_SECRET_NAME")
fi

# Derived values
MODEL_DIR_NAME=$(echo "$MODEL_ID" | tr '/' '_')
MODEL_PATH="${MODELS_DIR}/${MODEL_DIR_NAME}"

VERBOSE=""
[[ "${1:-}" == "--verbose" ]] && VERBOSE="1"

log_section "Validate Setup"

ERRORS=()
WARNINGS=()

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------
check_pass() {
    log_success "$1"
}

check_fail() {
    log_error "$1"
    ERRORS+=("$1")
}

check_warn() {
    log_warn "$1"
    WARNINGS+=("$1")
}

# -----------------------------------------------------------------------------
# NVMe Storage
# -----------------------------------------------------------------------------
log_subsection "NVMe Storage"

# Check mount point
if mountpoint -q "$NVME_MOUNT_PATH" 2>/dev/null; then
    check_pass "NVMe mounted at: $NVME_MOUNT_PATH"

    # Check available space
    AVAILABLE_GB=$(df -BG "$NVME_MOUNT_PATH" 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G')
    if [[ -n "$AVAILABLE_GB" ]] && [[ "$AVAILABLE_GB" -lt 10 ]]; then
        check_warn "Low disk space: ${AVAILABLE_GB}GB available"
    else
        check_pass "Disk space OK: ${AVAILABLE_GB}GB available"
    fi
else
    # Check if we're in a container (might not have direct mount visibility)
    if [[ -d "$NVME_MOUNT_PATH" ]] && [[ -w "$NVME_MOUNT_PATH" ]]; then
        check_warn "NVMe mount point exists but mountpoint check failed (may be OK in container)"
    else
        check_fail "NVMe not mounted at: $NVME_MOUNT_PATH"
    fi
fi

# Check models directory
if [[ -d "$MODELS_DIR" ]]; then
    if [[ -w "$MODELS_DIR" ]]; then
        check_pass "Models directory writable: $MODELS_DIR"
    else
        check_fail "Models directory not writable: $MODELS_DIR"
    fi
else
    check_fail "Models directory missing: $MODELS_DIR"
fi

# -----------------------------------------------------------------------------
# Model
# -----------------------------------------------------------------------------
log_subsection "Model"

if [[ -d "$MODEL_PATH" ]]; then
    check_pass "Model directory exists: $MODEL_PATH"

    # Check for config.json
    if [[ -f "$MODEL_PATH/config.json" ]]; then
        check_pass "Model config.json present"
    else
        check_fail "Model config.json missing"
    fi

    # Check for weight files
    WEIGHT_COUNT=$(find "$MODEL_PATH" -name "*.safetensors" -o -name "*.bin" 2>/dev/null | wc -l)
    if [[ "$WEIGHT_COUNT" -gt 0 ]]; then
        check_pass "Model weights present ($WEIGHT_COUNT files)"
    else
        check_fail "No model weight files found"
    fi

    # Check model size
    MODEL_SIZE=$(du -sh "$MODEL_PATH" 2>/dev/null | cut -f1)
    log_info "  Model size: $MODEL_SIZE"
else
    check_fail "Model not downloaded: $MODEL_PATH"
fi

# -----------------------------------------------------------------------------
# Kubernetes (if kubectl available)
# -----------------------------------------------------------------------------
if command -v kubectl &>/dev/null; then
    log_subsection "Kubernetes"

    if kubectl cluster-info &>/dev/null; then
        check_pass "Cluster connection OK"

        # Check namespace
        if kubectl get namespace "$K8S_NAMESPACE" &>/dev/null; then
            check_pass "Namespace exists: $K8S_NAMESPACE"
        else
            check_fail "Namespace missing: $K8S_NAMESPACE"
        fi

        # Check HF secret
        if kubectl get secret "$K8S_HF_SECRET_NAME" -n "$K8S_NAMESPACE" &>/dev/null; then
            check_pass "HuggingFace secret exists: $K8S_HF_SECRET_NAME"
        else
            check_warn "HuggingFace secret missing: $K8S_HF_SECRET_NAME"
        fi

        # Check for GPU nodes
        GPU_NODES=$(kubectl get nodes -l role=ai-gpu --no-headers 2>/dev/null | wc -l)
        if [[ "$GPU_NODES" -gt 0 ]]; then
            check_pass "GPU nodes available: $GPU_NODES"
        else
            check_warn "No GPU nodes found with label 'role=ai-gpu'"
        fi

        # Check NVIDIA device plugin
        NVIDIA_PODS=$(kubectl get pods -n kube-system -l name=nvidia-device-plugin-ds --no-headers 2>/dev/null | wc -l)
        if [[ "$NVIDIA_PODS" -gt 0 ]]; then
            check_pass "NVIDIA device plugin running"
        else
            check_warn "NVIDIA device plugin not detected"
        fi
    else
        check_warn "Cannot connect to Kubernetes cluster"
    fi
else
    log_info "kubectl not available, skipping Kubernetes checks"
fi

# -----------------------------------------------------------------------------
# AWS (if aws available)
# -----------------------------------------------------------------------------
if command -v aws &>/dev/null; then
    log_subsection "AWS"

    if aws sts get-caller-identity &>/dev/null; then
        check_pass "AWS credentials valid"

        # Check AppConfig access
        if [[ -n "${APPCONFIG_APPLICATION_ID:-}" ]]; then
            if aws appconfig get-application --application-id "$APPCONFIG_APPLICATION_ID" --region "${AWS_REGION:-us-east-1}" &>/dev/null; then
                check_pass "AppConfig accessible"
            else
                check_warn "Cannot access AppConfig application"
            fi
        else
            log_info "  AppConfig not configured"
        fi
    else
        check_warn "AWS credentials not configured or invalid"
    fi
else
    log_info "aws not available, skipping AWS checks"
fi

# -----------------------------------------------------------------------------
# GPU (if on node)
# -----------------------------------------------------------------------------
if command -v nvidia-smi &>/dev/null; then
    log_subsection "GPU"

    if nvidia-smi &>/dev/null; then
        GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null | head -1)
        check_pass "GPU available: $GPU_INFO"

        # Check CUDA
        if nvidia-smi --query-gpu=driver_version --format=csv,noheader &>/dev/null; then
            DRIVER_VERSION=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)
            check_pass "NVIDIA driver: $DRIVER_VERSION"
        fi
    else
        check_fail "nvidia-smi failed - GPU may not be accessible"
    fi
else
    log_info "nvidia-smi not available, skipping GPU checks"
fi

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
log_section "Validation Summary"

if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    log_warn "Warnings (${#WARNINGS[@]}):"
    for warn in "${WARNINGS[@]}"; do
        log_warn "  - $warn"
    done
    echo ""
fi

if [[ ${#ERRORS[@]} -gt 0 ]]; then
    log_error "Errors (${#ERRORS[@]}):"
    for err in "${ERRORS[@]}"; do
        log_error "  - $err"
    done
    echo ""
    log_error "Setup validation FAILED"
    exit 1
else
    if [[ ${#WARNINGS[@]} -gt 0 ]]; then
        log_warn "Setup validation PASSED with warnings"
    else
        log_success "Setup validation PASSED"
    fi
    exit 0
fi
