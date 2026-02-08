# ========================================================================
# BUDGETS MODULE - TERRAGRUNT WRAPPER
# Dependency Group 1: Foundation (no dependencies)
# Standalone module for cost monitoring
# ========================================================================

include "root" {
  path   = find_in_parent_folders("root.hcl")
  expose = true
}

terraform {
  source = "${include.root.locals.repo_root}/deploy/iac/terraform/budgets"
}

inputs = {
  # Core variables from root config
  aws_account_id = include.root.inputs.aws_account_id
  aws_region     = include.root.inputs.aws_region
  environment    = include.root.inputs.environment
  project_name   = include.root.inputs.project_name

  # Budget configuration
  budget_alert_email = include.root.inputs.budgets_config.alert_email
  budget_thresholds  = include.root.inputs.budgets_config.thresholds

  # Common tags
  common_tags = include.root.inputs.common_tags
}
