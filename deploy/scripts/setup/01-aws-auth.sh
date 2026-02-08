#!/bin/bash
# =============================================================================
# AWS AUTHENTICATION
# =============================================================================
# Authenticates to AWS and validates credentials.
# Supports: environment variables, credentials file, instance profile, SSO.
#
# Usage: ./setup/01-aws-auth.sh [--profile PROFILE] [--role ROLE_ARN]
#
# Options:
#   --profile   AWS CLI profile to use
#   --role      IAM role ARN to assume (for cross-account access)
# =============================================================================

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${SCRIPTS_DIR}/lib/logger.sh"
source "${SCRIPTS_DIR}/lib/common.sh"
source "${SCRIPTS_DIR}/config/defaults.env"

# Parse arguments
PROFILE=""
ROLE_ARN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            PROFILE="$2"
            shift 2
            ;;
        --role)
            ROLE_ARN="$2"
            shift 2
            ;;
        *)
            die "Unknown option: $1"
            ;;
    esac
done

log_section "AWS Authentication"

# -----------------------------------------------------------------------------
# Set profile if specified
# -----------------------------------------------------------------------------
if [[ -n "$PROFILE" ]]; then
    log_info "Using AWS profile: $PROFILE"
    export AWS_PROFILE="$PROFILE"
fi

# -----------------------------------------------------------------------------
# Check for existing credentials
# -----------------------------------------------------------------------------
log_subsection "Checking Credentials"

detect_auth_method() {
    if [[ -n "${AWS_ACCESS_KEY_ID:-}" ]] && [[ -n "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
        echo "environment"
    elif [[ -n "${AWS_PROFILE:-}" ]] && aws configure list --profile "${AWS_PROFILE}" &>/dev/null; then
        echo "profile"
    elif [[ -f ~/.aws/credentials ]] && aws configure list &>/dev/null; then
        echo "credentials-file"
    elif curl -s --connect-timeout 1 http://169.254.169.254/latest/meta-data/iam/ &>/dev/null; then
        echo "instance-profile"
    elif [[ -f ~/.aws/sso/cache/*.json ]] 2>/dev/null; then
        echo "sso"
    else
        echo "none"
    fi
}

AUTH_METHOD=$(detect_auth_method)
log_info "Detected auth method: $AUTH_METHOD"

case "$AUTH_METHOD" in
    environment)
        log_success "Using credentials from environment variables"
        ;;
    profile)
        log_success "Using AWS profile: ${AWS_PROFILE}"
        ;;
    credentials-file)
        log_success "Using credentials from ~/.aws/credentials"
        ;;
    instance-profile)
        log_success "Using EC2 instance profile"
        ;;
    sso)
        log_info "SSO detected, checking if session is valid..."
        if ! aws sts get-caller-identity &>/dev/null; then
            log_warn "SSO session expired, initiating login..."
            aws sso login --profile "${AWS_PROFILE:-default}"
        fi
        log_success "SSO session valid"
        ;;
    none)
        die "No AWS credentials found. Please configure credentials first."
        ;;
esac

# -----------------------------------------------------------------------------
# Assume role if specified
# -----------------------------------------------------------------------------
if [[ -n "$ROLE_ARN" ]]; then
    log_subsection "Assuming Role"
    log_info "Role: $ROLE_ARN"

    # Generate session name
    SESSION_NAME="judge-inference-$(date +%s)"

    # Assume role
    CREDENTIALS=$(aws sts assume-role \
        --role-arn "$ROLE_ARN" \
        --role-session-name "$SESSION_NAME" \
        --output json) || die "Failed to assume role: $ROLE_ARN"

    # Export credentials
    export AWS_ACCESS_KEY_ID=$(echo "$CREDENTIALS" | jq -r '.Credentials.AccessKeyId')
    export AWS_SECRET_ACCESS_KEY=$(echo "$CREDENTIALS" | jq -r '.Credentials.SecretAccessKey')
    export AWS_SESSION_TOKEN=$(echo "$CREDENTIALS" | jq -r '.Credentials.SessionToken')

    EXPIRATION=$(echo "$CREDENTIALS" | jq -r '.Credentials.Expiration')
    log_success "Role assumed successfully (expires: $EXPIRATION)"
fi

# -----------------------------------------------------------------------------
# Validate credentials
# -----------------------------------------------------------------------------
log_subsection "Validating Credentials"

if ! IDENTITY=$(aws sts get-caller-identity --output json 2>&1); then
    die "Failed to validate credentials: $IDENTITY"
fi

ACCOUNT_ID=$(echo "$IDENTITY" | jq -r '.Account')
USER_ARN=$(echo "$IDENTITY" | jq -r '.Arn')
USER_ID=$(echo "$IDENTITY" | jq -r '.UserId')

log_success "Credentials validated!"
log_info "  Account:  $ACCOUNT_ID"
log_info "  ARN:      $USER_ARN"
log_info "  User ID:  $USER_ID"

# -----------------------------------------------------------------------------
# Set region if not already set
# -----------------------------------------------------------------------------
if [[ -z "${AWS_REGION:-}" ]]; then
    if [[ -n "${AWS_DEFAULT_REGION:-}" ]]; then
        export AWS_REGION="$AWS_DEFAULT_REGION"
    elif CONFIGURED_REGION=$(aws configure get region 2>/dev/null); then
        export AWS_REGION="$CONFIGURED_REGION"
    else
        export AWS_REGION="us-east-1"
        log_warn "No region configured, defaulting to: $AWS_REGION"
    fi
fi

log_info "  Region:   $AWS_REGION"

# -----------------------------------------------------------------------------
# Export for other scripts
# -----------------------------------------------------------------------------
log_subsection "Exporting Configuration"

# Write to temp file for sourcing by other scripts
AUTH_ENV_FILE="/tmp/aws_auth.env"
cat > "$AUTH_ENV_FILE" <<EOF
export AWS_REGION="${AWS_REGION}"
export AWS_ACCOUNT_ID="${ACCOUNT_ID}"
EOF

if [[ -n "${AWS_ACCESS_KEY_ID:-}" ]]; then
    cat >> "$AUTH_ENV_FILE" <<EOF
export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}"
export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}"
EOF
    if [[ -n "${AWS_SESSION_TOKEN:-}" ]]; then
        echo "export AWS_SESSION_TOKEN=\"${AWS_SESSION_TOKEN}\"" >> "$AUTH_ENV_FILE"
    fi
fi

log_success "Auth configuration saved to: $AUTH_ENV_FILE"
log_info "Source with: source $AUTH_ENV_FILE"
