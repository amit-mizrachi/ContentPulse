#!/bin/bash
# =============================================================================
# TAIL LOGS
# =============================================================================
# Convenience script to tail logs from vLLM pods in Kubernetes.
#
# Usage: ./runtime/tail-logs.sh [--namespace NS] [--follow] [--lines N]
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
    K8S_SERVICE_NAME=$(appconfig_get "judge_inference.kubernetes.service_name" "$K8S_SERVICE_NAME")
fi

# Parse arguments
FOLLOW=""
LINES="100"

while [[ $# -gt 0 ]]; do
    case $1 in
        --namespace|-n)
            K8S_NAMESPACE="$2"
            shift 2
            ;;
        --follow|-f)
            FOLLOW="-f"
            shift
            ;;
        --lines|-l)
            LINES="$2"
            shift 2
            ;;
        --service|-s)
            K8S_SERVICE_NAME="$2"
            shift 2
            ;;
        *)
            die "Unknown option: $1"
            ;;
    esac
done

log_section "Tail Logs"

log_info "Namespace: $K8S_NAMESPACE"
log_info "Service:   $K8S_SERVICE_NAME"

# -----------------------------------------------------------------------------
# Check prerequisites
# -----------------------------------------------------------------------------
require_command kubectl || die "kubectl required"

if ! kubectl cluster-info &>/dev/null; then
    die "Cannot connect to Kubernetes cluster"
fi

# -----------------------------------------------------------------------------
# Find pods
# -----------------------------------------------------------------------------
log_subsection "Finding Pods"

# Try different label selectors
PODS=""

# Try app label
PODS=$(kubectl get pods -n "$K8S_NAMESPACE" -l "app=$K8S_SERVICE_NAME" -o name 2>/dev/null | head -1)

# Try app.kubernetes.io/name label
if [[ -z "$PODS" ]]; then
    PODS=$(kubectl get pods -n "$K8S_NAMESPACE" -l "app.kubernetes.io/name=$K8S_SERVICE_NAME" -o name 2>/dev/null | head -1)
fi

# Try name contains
if [[ -z "$PODS" ]]; then
    PODS=$(kubectl get pods -n "$K8S_NAMESPACE" -o name 2>/dev/null | grep -i "$K8S_SERVICE_NAME" | head -1)
fi

if [[ -z "$PODS" ]]; then
    log_error "No pods found for service: $K8S_SERVICE_NAME"
    log_info ""
    log_info "Available pods in namespace $K8S_NAMESPACE:"
    kubectl get pods -n "$K8S_NAMESPACE" --no-headers 2>/dev/null || true
    exit 1
fi

POD_NAME="${PODS#pod/}"
log_success "Found pod: $POD_NAME"

# -----------------------------------------------------------------------------
# Tail logs
# -----------------------------------------------------------------------------
log_subsection "Logs"

log_info "Showing last $LINES lines${FOLLOW:+ (following)}..."
echo ""

exec kubectl logs "$PODS" -n "$K8S_NAMESPACE" --tail="$LINES" $FOLLOW
