# ========================================================================
# VPC MODULE - TERRAGRUNT WRAPPER
# Dependency Group 1: Foundation (no dependencies)
# ========================================================================

include "root" {
  path   = find_in_parent_folders("root.hcl")
  expose = true
}

terraform {
  source = "${include.root.locals.repo_root}/deploy/iac/terraform/vpc"
}

inputs = {
  # Core variables from root config
  aws_account_id      = include.root.inputs.aws_account_id
  aws_region          = include.root.inputs.aws_region
  environment         = include.root.inputs.environment
  project_name        = include.root.inputs.project_name

  # VPC configuration from global config
  vpc_config = include.root.inputs.vpc_config

  # Common tags
  common_tags = include.root.inputs.common_tags
}
