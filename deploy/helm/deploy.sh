#!/bin/bash
# ========================================================================
# LLM Judge - Helm Deployment Script
# Deploys system components and application services to EKS
# ========================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="llm-judge"

# Parse arguments
SYSTEM_ONLY=false
APPS_ONLY=false
DRY_RUN=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --system-only) SYSTEM_ONLY=true ;;
        --apps-only) APPS_ONLY=true ;;
        --dry-run) DRY_RUN=true ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --system-only    Deploy only system components"
            echo "  --apps-only      Deploy only application services"
            echo "  --dry-run        Show what would be deployed without deploying"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

run_helm() {
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY-RUN] helm $@"
    else
        helm "$@"
    fi
}

# ========================================================================
# Add Helm Repositories
# ========================================================================
add_repos() {
    log_info "Adding Helm repositories..."
    helm repo add eks https://aws.github.io/eks-charts 2>/dev/null || true
    helm repo add external-secrets https://charts.external-secrets.io 2>/dev/null || true
    helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/ 2>/dev/null || true
    helm repo add autoscaler https://kubernetes.github.io/autoscaler 2>/dev/null || true
    helm repo update
}

# ========================================================================
# Deploy System Components
# ========================================================================
deploy_system() {
    log_info "Deploying system components..."

    # 1. Metrics Server (required for HPA)
    log_info "Deploying metrics-server..."
    run_helm upgrade --install metrics-server metrics-server/metrics-server \
        -n kube-system \
        -f "$SCRIPT_DIR/system/metrics-server-values.yaml" \
        --wait --timeout 5m

    # 2. AWS Load Balancer Controller (required for Ingress)
    log_info "Deploying aws-load-balancer-controller..."
    run_helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
        -n kube-system \
        -f "$SCRIPT_DIR/system/aws-lb-controller-values.yaml" \
        --wait --timeout 5m

    # 3. External Secrets Operator
    log_info "Deploying external-secrets..."
    run_helm upgrade --install external-secrets external-secrets/external-secrets \
        -n external-secrets-system \
        --create-namespace \
        -f "$SCRIPT_DIR/system/external-secrets-values.yaml" \
        --wait --timeout 5m

    # 4. Cluster Autoscaler
    log_info "Deploying cluster-autoscaler..."
    run_helm upgrade --install cluster-autoscaler autoscaler/cluster-autoscaler \
        -n kube-system \
        -f "$SCRIPT_DIR/system/cluster-autoscaler-values.yaml" \
        --wait --timeout 5m

    # 5. Apply ClusterSecretStore (after external-secrets is ready)
    log_info "Applying ClusterSecretStore..."
    if [ "$DRY_RUN" = false ]; then
        kubectl apply -f "$SCRIPT_DIR/system/secretstore.yaml"
    else
        echo "[DRY-RUN] kubectl apply -f $SCRIPT_DIR/system/secretstore.yaml"
    fi

    log_info "System components deployed successfully!"
}

# ========================================================================
# Deploy Application Services
# ========================================================================
deploy_apps() {
    log_info "Deploying application services..."

    # Create namespace if not exists
    if [ "$DRY_RUN" = false ]; then
        kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    else
        echo "[DRY-RUN] kubectl create namespace $NAMESPACE"
    fi

    # Deploy services in dependency order
    # Group 1: No dependencies
    log_info "Deploying redis-service..."
    run_helm upgrade --install redis-service "$SCRIPT_DIR/charts/llm-judge-service" \
        -n "$NAMESPACE" \
        -f "$SCRIPT_DIR/releases/redis-service-values.yaml" \
        --wait --timeout 5m

    log_info "Deploying persistence-service..."
    run_helm upgrade --install persistence-service "$SCRIPT_DIR/charts/llm-judge-service" \
        -n "$NAMESPACE" \
        -f "$SCRIPT_DIR/releases/persistence-values.yaml" \
        --wait --timeout 5m

    # Group 2: Depends on redis-service
    log_info "Deploying gateway-service..."
    run_helm upgrade --install gateway-service "$SCRIPT_DIR/charts/llm-judge-service" \
        -n "$NAMESPACE" \
        -f "$SCRIPT_DIR/releases/gateway-values.yaml" \
        --wait --timeout 5m

    log_info "Deploying inference-service..."
    run_helm upgrade --install inference-service "$SCRIPT_DIR/charts/llm-judge-service" \
        -n "$NAMESPACE" \
        -f "$SCRIPT_DIR/releases/inference-values.yaml" \
        --wait --timeout 5m

    # Group 3: Depends on redis-service and persistence-service
    log_info "Deploying judge-service..."
    run_helm upgrade --install judge-service "$SCRIPT_DIR/charts/llm-judge-service" \
        -n "$NAMESPACE" \
        -f "$SCRIPT_DIR/releases/judge-values.yaml" \
        --wait --timeout 5m

    log_info "Application services deployed successfully!"
}

# ========================================================================
# Main
# ========================================================================
main() {
    log_info "LLM Judge Helm Deployment"
    log_info "========================="

    # Check kubectl context
    CURRENT_CONTEXT=$(kubectl config current-context)
    log_info "Using kubectl context: $CURRENT_CONTEXT"

    if [ "$DRY_RUN" = true ]; then
        log_warn "DRY RUN MODE - No changes will be made"
    fi

    # Add repos
    add_repos

    # Deploy based on flags
    if [ "$APPS_ONLY" = true ]; then
        deploy_apps
    elif [ "$SYSTEM_ONLY" = true ]; then
        deploy_system
    else
        deploy_system
        deploy_apps
    fi

    log_info "Deployment complete!"

    if [ "$DRY_RUN" = false ]; then
        echo ""
        log_info "Checking pod status..."
        kubectl get pods -n kube-system -l "app.kubernetes.io/name in (aws-load-balancer-controller,metrics-server,cluster-autoscaler)"
        kubectl get pods -n external-secrets-system
        kubectl get pods -n "$NAMESPACE"
    fi
}

main "$@"
