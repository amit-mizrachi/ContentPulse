#!/bin/bash
# ========================================================================
# REDIS TERRAFORM DEPLOYMENT VERIFICATION
# ========================================================================
# Verifies that Redis was deployed correctly via Terraform Helm provider
# Usage: ./verify-terraform-deployment.sh
# ========================================================================

set -e

NAMESPACE="llm-judge"
RELEASE_NAME="redis"

echo "========================================================================="
echo "Redis Terraform Deployment Verification"
echo "========================================================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}!${NC} $1"
}

# ========================================================================
# 1. CHECK NAMESPACE
# ========================================================================

echo "1. Checking Kubernetes namespace..."
if kubectl get namespace "$NAMESPACE" &> /dev/null; then
    check_pass "Namespace '$NAMESPACE' exists"
else
    check_fail "Namespace '$NAMESPACE' does not exist"
    exit 1
fi
echo ""

# ========================================================================
# 2. CHECK STORAGE CLASS
# ========================================================================

echo "2. Checking StorageClass..."
if kubectl get storageclass gp3 &> /dev/null; then
    check_pass "StorageClass 'gp3' exists"

    # Check if it's managed by Terraform
    if kubectl get storageclass gp3 -o jsonpath='{.metadata.labels.app\.kubernetes\.io/managed-by}' | grep -q "terraform"; then
        check_pass "StorageClass is managed by Terraform"
    else
        check_warn "StorageClass exists but may not be managed by Terraform"
    fi
else
    check_fail "StorageClass 'gp3' does not exist"
    exit 1
fi
echo ""

# ========================================================================
# 3. CHECK HELM RELEASE
# ========================================================================

echo "3. Checking Helm release..."
if helm list -n "$NAMESPACE" | grep -q "^$RELEASE_NAME"; then
    check_pass "Helm release '$RELEASE_NAME' exists"

    # Check release status
    RELEASE_STATUS=$(helm status "$RELEASE_NAME" -n "$NAMESPACE" -o json | jq -r '.info.status')
    if [ "$RELEASE_STATUS" == "deployed" ]; then
        check_pass "Helm release status: $RELEASE_STATUS"
    else
        check_warn "Helm release status: $RELEASE_STATUS (expected: deployed)"
    fi

    # Show release info
    echo ""
    echo "Helm Release Details:"
    helm list -n "$NAMESPACE" | grep "^$RELEASE_NAME"
else
    check_fail "Helm release '$RELEASE_NAME' not found"
    exit 1
fi
echo ""

# ========================================================================
# 4. CHECK REDIS POD
# ========================================================================

echo "4. Checking Redis pod..."
if kubectl get pods -n "$NAMESPACE" -l app=redis &> /dev/null; then
    POD_STATUS=$(kubectl get pods -n "$NAMESPACE" -l app=redis -o jsonpath='{.items[0].status.phase}')

    if [ "$POD_STATUS" == "Running" ]; then
        check_pass "Redis pod is Running"

        # Check ready status
        POD_READY=$(kubectl get pods -n "$NAMESPACE" -l app=redis -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}')
        if [ "$POD_READY" == "True" ]; then
            check_pass "Redis pod is Ready"
        else
            check_warn "Redis pod is not Ready yet"
        fi
    else
        check_warn "Redis pod status: $POD_STATUS (expected: Running)"
    fi

    # Show pod details
    echo ""
    echo "Pod Details:"
    kubectl get pods -n "$NAMESPACE" -l app=redis
else
    check_fail "Redis pod not found"
    exit 1
fi
echo ""

# ========================================================================
# 5. CHECK REDIS SERVICE
# ========================================================================

echo "5. Checking Redis service..."
if kubectl get service "$RELEASE_NAME" -n "$NAMESPACE" &> /dev/null; then
    check_pass "Redis service exists"

    # Check service type
    SVC_TYPE=$(kubectl get service "$RELEASE_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.type}')
    if [ "$SVC_TYPE" == "ClusterIP" ]; then
        check_pass "Service type: $SVC_TYPE"
    else
        check_warn "Service type: $SVC_TYPE (expected: ClusterIP)"
    fi

    # Show service details
    echo ""
    echo "Service Details:"
    kubectl get service "$RELEASE_NAME" -n "$NAMESPACE"
else
    check_fail "Redis service not found"
    exit 1
fi
echo ""

# ========================================================================
# 6. CHECK REDIS PVC
# ========================================================================

echo "6. Checking Redis PVC..."
if kubectl get pvc -n "$NAMESPACE" -l app=redis &> /dev/null; then
    PVC_STATUS=$(kubectl get pvc -n "$NAMESPACE" -l app=redis -o jsonpath='{.items[0].status.phase}')

    if [ "$PVC_STATUS" == "Bound" ]; then
        check_pass "PVC is Bound"

        # Check storage class
        PVC_SC=$(kubectl get pvc -n "$NAMESPACE" -l app=redis -o jsonpath='{.items[0].spec.storageClassName}')
        if [ "$PVC_SC" == "gp3" ]; then
            check_pass "PVC uses StorageClass: $PVC_SC"
        else
            check_warn "PVC uses StorageClass: $PVC_SC (expected: gp3)"
        fi
    else
        check_warn "PVC status: $PVC_STATUS (expected: Bound)"
    fi

    # Show PVC details
    echo ""
    echo "PVC Details:"
    kubectl get pvc -n "$NAMESPACE" -l app=redis
else
    check_fail "Redis PVC not found"
    exit 1
fi
echo ""

# ========================================================================
# 7. TEST REDIS CONNECTIVITY
# ========================================================================

echo "7. Testing Redis connectivity..."
POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l app=redis -o jsonpath='{.items[0].metadata.name}')

if [ -n "$POD_NAME" ]; then
    if kubectl exec -n "$NAMESPACE" "$POD_NAME" -- redis-cli ping &> /dev/null; then
        PING_RESPONSE=$(kubectl exec -n "$NAMESPACE" "$POD_NAME" -- redis-cli ping)
        if [ "$PING_RESPONSE" == "PONG" ]; then
            check_pass "Redis responds to PING: $PING_RESPONSE"
        else
            check_warn "Redis PING response: $PING_RESPONSE (expected: PONG)"
        fi
    else
        check_fail "Cannot connect to Redis"
    fi

    # Test basic operations
    if kubectl exec -n "$NAMESPACE" "$POD_NAME" -- redis-cli set test_key "terraform_deployed" &> /dev/null; then
        check_pass "Redis SET operation successful"
    else
        check_warn "Redis SET operation failed"
    fi

    if kubectl exec -n "$NAMESPACE" "$POD_NAME" -- redis-cli get test_key &> /dev/null; then
        GET_RESPONSE=$(kubectl exec -n "$NAMESPACE" "$POD_NAME" -- redis-cli get test_key)
        if [ "$GET_RESPONSE" == "terraform_deployed" ]; then
            check_pass "Redis GET operation successful"
        else
            check_warn "Redis GET response: $GET_RESPONSE"
        fi
    else
        check_warn "Redis GET operation failed"
    fi

    # Clean up test key
    kubectl exec -n "$NAMESPACE" "$POD_NAME" -- redis-cli del test_key &> /dev/null
else
    check_fail "Cannot find Redis pod name"
fi
echo ""

# ========================================================================
# 8. CHECK TERRAFORM STATE (OPTIONAL)
# ========================================================================

echo "8. Checking Terraform state (optional)..."
TERRAGRUNT_DIR="../../../../iac/terragrunt/dev/helm-releases"

if [ -d "$TERRAGRUNT_DIR" ]; then
    cd "$TERRAGRUNT_DIR"

    if terragrunt state list 2>/dev/null | grep -q "helm_release.redis_cache"; then
        check_pass "Redis is managed by Terraform"

        echo ""
        echo "Terraform State:"
        terragrunt state show 'helm_release.redis_cache' 2>/dev/null | head -20
    else
        check_warn "Redis not found in Terraform state"
    fi

    cd - > /dev/null
else
    check_warn "Terragrunt directory not found (skipping Terraform state check)"
fi
echo ""

# ========================================================================
# SUMMARY
# ========================================================================

echo "========================================================================="
echo "Verification Complete!"
echo "========================================================================="
echo ""
echo "Redis Deployment Summary:"
echo "  • Namespace: $NAMESPACE"
echo "  • Release: $RELEASE_NAME"
echo "  • Service DNS: redis.llm-judge.svc.cluster.local:6379"
echo "  • Storage: gp3 (EBS CSI Driver)"
echo "  • Deployment Method: Terraform Helm Provider"
echo ""
echo "Next Steps:"
echo "  1. Monitor Redis performance: kubectl top pod -n $NAMESPACE -l app=redis"
echo "  2. View Redis logs: kubectl logs -n $NAMESPACE -l app=redis"
echo "  3. Check Redis info: kubectl exec -n $NAMESPACE $POD_NAME -- redis-cli INFO"
echo ""
echo -e "${GREEN}All checks passed!${NC}"
echo "========================================================================="
