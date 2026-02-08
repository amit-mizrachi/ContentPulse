# ========================================================================
# PROVIDERS - K8S CONFIG MODULE
# ========================================================================
# Requires kubernetes provider to be configured in the root module
# ========================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.20"
    }
  }
}
