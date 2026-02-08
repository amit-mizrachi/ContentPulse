#!/bin/bash
# =============================================================================
# CREATE KUBERNETES SECRETS
# =============================================================================
# Creates required Kubernetes secrets for the judge inference service.
#
# Usage: ./setup/04-create-k8s-secrets.sh [--namespace NS] [--hf-token TOKEN]
#
# Configuration (from environment or AppConfig):
#   K8S_NAMESPACE      - Kubernetes namespace (default: llm-judge)
#   K8S_HF_SECRET_NAME - Secret name for HF token (default: hf-secret)
#   HF_TOKEN           - HuggingFace API token
# =============================================================================

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${SCRIPTS_DIR}/lib/logger.sh"
source "${SCRIPTS_DIR}/lib/common.sh"
source "${SCRIPTS_DIR}/config/defaults.env"

# Load AppConfig if available
if [[ -f /tmp/appconfig_cache.json ]]; then
    source "${SCRIPTS_DIR}/lib/appconfig.sh"
    K8S_NAMESPACE=$(appconfig_get "judge_inference.kubernetes.namespace" "$K8S_NAMESPACE")
    K8S_HF_SECRET_NAME=$(appconfig_get "judge_inference.kubernetes.hf_secret_name" "$K8S_HF_SECRET_NAME")
fi

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --namespace)
            K8S_NAMESPACE="$2"
            shift 2
            ;;
        --hf-token)
            HF_TOKEN="$2"
            shift 2
            ;;
        *)
            die "Unknown option: $1"
            ;;
    esac
done

log_section "Create Kubernetes Secrets"

log_info "Namespace:   $K8S_NAMESPACE"
log_info "Secret name: $K8S_HF_SECRET_NAME"

# -----------------------------------------------------------------------------
# Check prerequisites
# -----------------------------------------------------------------------------
log_subsection "Checking Prerequisites"

require_command kubectl || die "kubectl required"

# Check cluster connection
if ! kubectl cluster-info &>/dev/null; then
    die "Cannot connect to Kubernetes cluster"
fi
log_success "Kubernetes cluster connected"

# -----------------------------------------------------------------------------
# Ensure namespace exists
# -----------------------------------------------------------------------------
log_subsection "Checking Namespace"

if kubectl get namespace "$K8S_NAMESPACE" &>/dev/null; then
    log_success "Namespace exists: $K8S_NAMESPACE"
else
    log_info "Creating namespace: $K8S_NAMESPACE"
    kubectl create namespace "$K8S_NAMESPACE" || die "Failed to create namespace"
    log_success "Namespace created"
fi

# -----------------------------------------------------------------------------
# Get HuggingFace token
# -----------------------------------------------------------------------------
log_subsection "HuggingFace Token"

if [[ -z "${HF_TOKEN:-}" ]]; then
    # Try to get from environment
    HF_TOKEN="${HUGGING_FACE_HUB_TOKEN:-}"
fi

if [[ -z "${HF_TOKEN:-}" ]]; then
    # Try to get from huggingface CLI config
    HF_TOKEN_FILE="$HOME/.cache/huggingface/token"
    if [[ -f "$HF_TOKEN_FILE" ]]; then
        HF_TOKEN=$(cat "$HF_TOKEN_FILE")
        log_info "Using token from: $HF_TOKEN_FILE"
    fi
fi

if [[ -z "${HF_TOKEN:-}" ]]; then
    log_warn "No HuggingFace token found"
    log_info ""
    log_info "To set the token, either:"
    log_info "  1. Pass it as an argument: --hf-token YOUR_TOKEN"
    log_info "  2. Set environment variable: export HF_TOKEN=YOUR_TOKEN"
    log_info "  3. Login with HuggingFace CLI: huggingface-cli login"
    log_info ""
    log_info "Get your token at: https://huggingface.co/settings/tokens"
    log_info ""

    # Prompt for token
    echo -n "Enter HuggingFace token (or press Enter to skip): "
    read -r -s HF_TOKEN
    echo ""

    if [[ -z "$HF_TOKEN" ]]; then
        log_warn "Skipping HuggingFace secret creation"
        log_info "You can create it later with:"
        log_info "  kubectl create secret generic $K8S_HF_SECRET_NAME \\"
        log_info "    --from-literal=token=YOUR_TOKEN \\"
        log_info "    -n $K8S_NAMESPACE"
        exit 0
    fi
fi

# Validate token format (basic check)
if [[ ! "$HF_TOKEN" =~ ^hf_ ]]; then
    log_warn "Token doesn't start with 'hf_' - this may not be a valid HuggingFace token"
fi

log_success "HuggingFace token provided"

# -----------------------------------------------------------------------------
# Create or update secret
# -----------------------------------------------------------------------------
log_subsection "Creating Secret"

if kubectl get secret "$K8S_HF_SECRET_NAME" -n "$K8S_NAMESPACE" &>/dev/null; then
    log_info "Secret already exists, updating..."

    # Delete and recreate (simplest way to update)
    kubectl delete secret "$K8S_HF_SECRET_NAME" -n "$K8S_NAMESPACE" || true
fi

kubectl create secret generic "$K8S_HF_SECRET_NAME" \
    --from-literal=token="$HF_TOKEN" \
    -n "$K8S_NAMESPACE" || die "Failed to create secret"

log_success "Secret created: $K8S_HF_SECRET_NAME"

# -----------------------------------------------------------------------------
# Verify secret
# -----------------------------------------------------------------------------
log_subsection "Verifying Secret"

SECRET_DATA=$(kubectl get secret "$K8S_HF_SECRET_NAME" -n "$K8S_NAMESPACE" -o jsonpath='{.data.token}' 2>/dev/null)

if [[ -n "$SECRET_DATA" ]]; then
    log_success "Secret verified: token key exists"
else
    log_warn "Secret created but token key not found"
fi

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
log_subsection "Summary"

log_success "Kubernetes secrets configured!"
log_info "  Namespace: $K8S_NAMESPACE"
log_info "  Secret:    $K8S_HF_SECRET_NAME"
log_info ""
log_info "Pods can access the token with:"
log_info "  env:"
log_info "    - name: HF_TOKEN"
log_info "      valueFrom:"
log_info "        secretKeyRef:"
log_info "          name: $K8S_HF_SECRET_NAME"
log_info "          key: token"
