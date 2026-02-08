#!/bin/bash
# =============================================================================
# MASTER DEPLOYMENT SCRIPT
# =============================================================================
# Orchestrates the deployment of the Judge Inference Service.
#
# Usage:
#   ./deploy.sh                    # Run all phases
#   ./deploy.sh --phase setup      # Run setup only
#   ./deploy.sh --phase runtime    # Run runtime only
#   ./deploy.sh --phase validate   # Run validation only
#
# Phases:
#   setup    - Prerequisites, AWS auth, NVMe mount, model download, K8s secrets
#   runtime  - Start vLLM, warmup model
#   validate - Verify everything is working
#   all      - Run setup + runtime + validate (default)
#
# Options:
#   --phase PHASE    Which phase to run (setup|runtime|validate|all)
#   --skip-auth      Skip AWS authentication (use existing credentials)
#   --skip-mount     Skip NVMe mount (already mounted)
#   --skip-download  Skip model download (already downloaded)
#   --namespace NS   Kubernetes namespace
#   --verbose        Enable verbose logging
#   --dry-run        Show what would be done without doing it
# =============================================================================

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPTS_DIR}/lib/logger.sh"
source "${SCRIPTS_DIR}/lib/common.sh"
source "${SCRIPTS_DIR}/config/defaults.env"

# -----------------------------------------------------------------------------
# Parse Arguments
# -----------------------------------------------------------------------------
PHASE="all"
SKIP_AUTH=""
SKIP_MOUNT=""
SKIP_DOWNLOAD=""
DRY_RUN=""
VERBOSE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --phase)
            PHASE="$2"
            shift 2
            ;;
        --skip-auth)
            SKIP_AUTH="1"
            shift
            ;;
        --skip-mount)
            SKIP_MOUNT="1"
            shift
            ;;
        --skip-download)
            SKIP_DOWNLOAD="1"
            shift
            ;;
        --namespace)
            K8S_NAMESPACE="$2"
            export K8S_NAMESPACE
            shift 2
            ;;
        --verbose|-v)
            VERBOSE="1"
            export LOG_LEVEL="DEBUG"
            shift
            ;;
        --dry-run)
            DRY_RUN="1"
            shift
            ;;
        --help|-h)
            head -30 "$0" | grep -E "^#" | sed 's/^# //' | sed 's/^#//'
            exit 0
            ;;
        *)
            die "Unknown option: $1\nUse --help for usage information."
            ;;
    esac
done

# Validate phase
case "$PHASE" in
    setup|runtime|validate|all) ;;
    *) die "Invalid phase: $PHASE (must be setup|runtime|validate|all)" ;;
esac

# -----------------------------------------------------------------------------
# Banner
# -----------------------------------------------------------------------------
echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                    JUDGE INFERENCE SERVICE DEPLOYMENT                      ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""

log_info "Phase:     $PHASE"
log_info "Namespace: ${K8S_NAMESPACE:-default}"
log_info "Verbose:   ${VERBOSE:-no}"
log_info "Dry run:   ${DRY_RUN:-no}"
echo ""

if [[ -n "$DRY_RUN" ]]; then
    log_warn "DRY RUN MODE - Commands will be shown but not executed"
    echo ""
fi

# Helper to run or show command
run_script() {
    local script="$1"
    shift
    local args=("$@")

    if [[ -n "$DRY_RUN" ]]; then
        log_info "[DRY RUN] Would execute: $script ${args[*]:-}"
        return 0
    fi

    if [[ -x "$script" ]]; then
        "$script" "${args[@]:-}"
    else
        bash "$script" "${args[@]:-}"
    fi
}

# -----------------------------------------------------------------------------
# Phase: Setup
# -----------------------------------------------------------------------------
run_setup() {
    log_section "PHASE: SETUP"

    # Step 1: Check prerequisites
    log_subsection "Step 1/5: Check Prerequisites"
    run_script "${SCRIPTS_DIR}/setup/00-check-prereqs.sh"

    # Step 2: AWS Authentication
    log_subsection "Step 2/5: AWS Authentication"
    if [[ -n "$SKIP_AUTH" ]]; then
        log_info "Skipping AWS auth (--skip-auth)"
    else
        run_script "${SCRIPTS_DIR}/setup/01-aws-auth.sh"
    fi

    # Step 3: Fetch Configuration
    log_subsection "Step 3/5: Fetch Configuration"
    run_script "${SCRIPTS_DIR}/fetch-config.sh"
    # Source the config for subsequent steps
    [[ -f /tmp/judge_inference_config.env ]] && source /tmp/judge_inference_config.env

    # Step 4: Mount NVMe (if on node)
    log_subsection "Step 4/5: Mount NVMe"
    if [[ -n "$SKIP_MOUNT" ]]; then
        log_info "Skipping NVMe mount (--skip-mount)"
    elif is_ec2_instance; then
        log_info "Running on EC2, attempting NVMe mount..."
        run_script "${SCRIPTS_DIR}/setup/02-mount-nvme.sh" || log_warn "NVMe mount failed (may need root)"
    else
        log_info "Not on EC2, skipping NVMe mount"
        log_info "Ensure NVMe is mounted via node user-data or privileged pod"
    fi

    # Step 5: Download Model
    log_subsection "Step 5/5: Download Model"
    if [[ -n "$SKIP_DOWNLOAD" ]]; then
        log_info "Skipping model download (--skip-download)"
    else
        run_script "${SCRIPTS_DIR}/setup/03-download-model.sh"
    fi

    # Step 6: Create K8s Secrets
    log_subsection "Step 6/5: Create Kubernetes Secrets"
    if command -v kubectl &>/dev/null && kubectl cluster-info &>/dev/null; then
        run_script "${SCRIPTS_DIR}/setup/04-create-k8s-secrets.sh"
    else
        log_info "kubectl not available or not connected, skipping K8s secrets"
    fi

    log_success "Setup phase complete!"
}

# -----------------------------------------------------------------------------
# Phase: Runtime
# -----------------------------------------------------------------------------
run_runtime() {
    log_section "PHASE: RUNTIME"

    # Source config
    [[ -f /tmp/judge_inference_config.env ]] && source /tmp/judge_inference_config.env

    # Start vLLM
    log_subsection "Starting vLLM Server"
    log_info "This will start the vLLM server in the foreground."
    log_info "In Kubernetes, this script is the container entrypoint."
    log_info ""

    if [[ -n "$DRY_RUN" ]]; then
        log_info "[DRY RUN] Would execute: runtime/start-vllm.sh"
        return 0
    fi

    # In a real deployment, this would be the container entrypoint
    # For manual testing, we can start it
    if confirm "Start vLLM server now? (This will block the terminal)" "n"; then
        run_script "${SCRIPTS_DIR}/runtime/start-vllm.sh"
    else
        log_info "Skipped. Start manually with: ./runtime/start-vllm.sh"
    fi
}

# -----------------------------------------------------------------------------
# Phase: Validate
# -----------------------------------------------------------------------------
run_validate() {
    log_section "PHASE: VALIDATE"

    # Source config
    [[ -f /tmp/judge_inference_config.env ]] && source /tmp/judge_inference_config.env

    run_script "${SCRIPTS_DIR}/setup/05-validate-setup.sh"

    # If vLLM is running, do health check
    if curl -s "http://localhost:${VLLM_PORT:-8000}/health" &>/dev/null; then
        log_subsection "Runtime Health Check"
        run_script "${SCRIPTS_DIR}/runtime/health-check.sh" --verbose
    fi

    log_success "Validation complete!"
}

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------
case "$PHASE" in
    setup)
        run_setup
        ;;
    runtime)
        run_runtime
        ;;
    validate)
        run_validate
        ;;
    all)
        run_setup
        echo ""
        run_validate
        echo ""
        log_section "DEPLOYMENT COMPLETE"
        log_success "Judge Inference Service is ready!"
        log_info ""
        log_info "Next steps:"
        log_info "  1. Deploy to Kubernetes:"
        log_info "     helm upgrade --install judge-inference ./helm/charts/llm-judge-service \\"
        log_info "       -f ./helm/releases/judge-inference-values.yaml -n ${K8S_NAMESPACE:-llm-judge}"
        log_info ""
        log_info "  2. Or start locally for testing:"
        log_info "     ./runtime/start-vllm.sh"
        log_info ""
        log_info "  3. Monitor logs:"
        log_info "     ./runtime/tail-logs.sh -f"
        ;;
esac

echo ""
log_info "Done!"
