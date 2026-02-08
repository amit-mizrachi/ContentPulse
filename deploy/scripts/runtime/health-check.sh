#!/bin/bash
# =============================================================================
# HEALTH CHECK
# =============================================================================
# Checks if the vLLM server is healthy and ready to serve requests.
# Returns exit code 0 if healthy, non-zero otherwise.
#
# Usage: ./runtime/health-check.sh [--host HOST] [--port PORT] [--timeout SECS]
#
# This script is designed to be used as a Kubernetes liveness/readiness probe.
# =============================================================================

set -uo pipefail

# Minimal logging for probe use (no external dependencies)
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Load defaults
VLLM_HOST="${VLLM_HOST:-localhost}"
VLLM_PORT="${VLLM_PORT:-8000}"
TIMEOUT="${TIMEOUT:-5}"

# Load from config if available
if [[ -f "${SCRIPTS_DIR}/config/defaults.env" ]]; then
    source "${SCRIPTS_DIR}/config/defaults.env"
fi

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            VLLM_HOST="$2"
            shift 2
            ;;
        --port)
            VLLM_PORT="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --verbose|-v)
            VERBOSE="1"
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

VERBOSE="${VERBOSE:-}"
BASE_URL="http://${VLLM_HOST}:${VLLM_PORT}"

# -----------------------------------------------------------------------------
# Check health endpoint
# -----------------------------------------------------------------------------
check_health() {
    local response
    local http_code

    # Try /health endpoint first (vLLM standard)
    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        --connect-timeout "$TIMEOUT" \
        --max-time "$TIMEOUT" \
        "${BASE_URL}/health" 2>/dev/null) || http_code="000"

    if [[ "$http_code" == "200" ]]; then
        [[ -n "$VERBOSE" ]] && echo "Health check passed: /health returned 200"
        return 0
    fi

    # Fallback: try /v1/models endpoint
    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        --connect-timeout "$TIMEOUT" \
        --max-time "$TIMEOUT" \
        "${BASE_URL}/v1/models" 2>/dev/null) || http_code="000"

    if [[ "$http_code" == "200" ]]; then
        [[ -n "$VERBOSE" ]] && echo "Health check passed: /v1/models returned 200"
        return 0
    fi

    [[ -n "$VERBOSE" ]] && echo "Health check failed: HTTP $http_code"
    return 1
}

# -----------------------------------------------------------------------------
# Check model is loaded (more thorough check)
# -----------------------------------------------------------------------------
check_model_loaded() {
    local response

    response=$(curl -s \
        --connect-timeout "$TIMEOUT" \
        --max-time "$TIMEOUT" \
        "${BASE_URL}/v1/models" 2>/dev/null) || return 1

    # Check if response contains model data
    if echo "$response" | grep -q '"data"' 2>/dev/null; then
        local model_count
        model_count=$(echo "$response" | grep -o '"id"' | wc -l)
        if [[ "$model_count" -gt 0 ]]; then
            [[ -n "$VERBOSE" ]] && echo "Model loaded: $model_count model(s) available"
            return 0
        fi
    fi

    [[ -n "$VERBOSE" ]] && echo "No models loaded"
    return 1
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if check_health && check_model_loaded; then
    [[ -n "$VERBOSE" ]] && echo "vLLM is healthy and ready"
    exit 0
else
    [[ -n "$VERBOSE" ]] && echo "vLLM is not ready"
    exit 1
fi
