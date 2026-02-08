#!/bin/bash
# =============================================================================
# CHECK PREREQUISITES
# =============================================================================
# Verifies that all required tools are installed.
#
# Usage: ./setup/00-check-prereqs.sh
# =============================================================================

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${SCRIPTS_DIR}/lib/logger.sh"
source "${SCRIPTS_DIR}/lib/common.sh"

log_section "Checking Prerequisites"

ERRORS=()

# -----------------------------------------------------------------------------
# Required CLI tools
# -----------------------------------------------------------------------------
log_subsection "CLI Tools"

check_tool() {
    local tool="$1"
    local install_hint="$2"

    if command -v "$tool" &>/dev/null; then
        local version
        version=$("$tool" --version 2>&1 | head -n1 || echo "unknown")
        log_success "$tool: $version"
        return 0
    else
        log_error "$tool: NOT FOUND"
        log_info "  Install: $install_hint"
        ERRORS+=("$tool")
        return 1
    fi
}

check_tool "aws" "pip install awscli OR brew install awscli"
check_tool "kubectl" "https://kubernetes.io/docs/tasks/tools/"
check_tool "helm" "https://helm.sh/docs/intro/install/"
check_tool "jq" "apt-get install jq OR brew install jq"
check_tool "curl" "apt-get install curl OR brew install curl"

# Python is optional but useful
if command -v python3 &>/dev/null; then
    version=$(python3 --version 2>&1)
    log_success "python3: $version"
else
    log_warn "python3: NOT FOUND (optional, needed for some operations)"
fi

# -----------------------------------------------------------------------------
# AWS Configuration
# -----------------------------------------------------------------------------
log_subsection "AWS Configuration"

# Check for credentials
if [[ -n "${AWS_ACCESS_KEY_ID:-}" ]] && [[ -n "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
    log_success "AWS credentials: Found in environment"
elif [[ -f ~/.aws/credentials ]]; then
    log_success "AWS credentials: Found in ~/.aws/credentials"
elif curl -s --connect-timeout 1 http://169.254.169.254/latest/meta-data/ &>/dev/null; then
    log_success "AWS credentials: Instance profile available"
else
    log_warn "AWS credentials: Not configured"
    log_info "  Configure with: aws configure"
    ERRORS+=("aws-credentials")
fi

# Check region
if [[ -n "${AWS_REGION:-}" ]]; then
    log_success "AWS region: $AWS_REGION (from environment)"
elif [[ -n "${AWS_DEFAULT_REGION:-}" ]]; then
    log_success "AWS region: $AWS_DEFAULT_REGION (from environment)"
elif aws configure get region &>/dev/null; then
    region=$(aws configure get region)
    log_success "AWS region: $region (from config)"
else
    log_warn "AWS region: Not configured"
    log_info "  Set with: export AWS_REGION=us-east-1"
fi

# -----------------------------------------------------------------------------
# Kubernetes Configuration
# -----------------------------------------------------------------------------
log_subsection "Kubernetes Configuration"

if [[ -f ~/.kube/config ]] || [[ -n "${KUBECONFIG:-}" ]]; then
    if kubectl cluster-info &>/dev/null; then
        context=$(kubectl config current-context 2>/dev/null || echo "unknown")
        log_success "Kubernetes: Connected (context: $context)"
    else
        log_warn "Kubernetes: Config exists but cannot connect"
        log_info "  Check your cluster connection"
    fi
else
    log_warn "Kubernetes: No config found"
    log_info "  Configure with: aws eks update-kubeconfig --name <cluster>"
fi

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
log_subsection "Summary"

if [[ ${#ERRORS[@]} -eq 0 ]]; then
    log_success "All prerequisites satisfied!"
    exit 0
else
    log_error "Missing prerequisites: ${ERRORS[*]}"
    log_info "Please install missing tools before continuing."
    exit 1
fi
