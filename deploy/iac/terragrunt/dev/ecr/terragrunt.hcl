# ========================================================================
# ECR MODULE - TERRAGRUNT WRAPPER
# Dependency Group 1: Foundational (no dependencies)
# ========================================================================

include "root" {
  path   = find_in_parent_folders("root.hcl")
  expose = true
}

terraform {
  source = "${include.root.locals.repo_root}/deploy/iac/terraform/ecr"
}

inputs = {
  # Core variables
  aws_account_id     = include.root.inputs.aws_account_id
  aws_region         = include.root.inputs.aws_region
  environment         = include.root.inputs.environment
  project_name       = include.root.inputs.project_name

  # ECR configuration
  repository_names = [
    "gateway-service",
    "inference-service",
    "judge-service",
    "redis-service",
    "persistence-service",
    "ai-model-service"
  ]

  common_tags = include.root.inputs.common_tags
}
