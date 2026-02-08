# ========================================================================
# SNS MODULE - TERRAGRUNT WRAPPER
# Dependency Group 1: Foundational (no dependencies)
# ========================================================================

include "root" {
  path   = find_in_parent_folders("root.hcl")
  expose = true
}

terraform {
  source = "${include.root.locals.repo_root}/deploy/iac/terraform/sns"
}

inputs = {
  # Core variables
  aws_account_id     = include.root.inputs.aws_account_id
  aws_region         = include.root.inputs.aws_region
  environment         = include.root.inputs.environment

  # SNS configuration
  sns_topic_names = toset(include.root.inputs.sns_config.topic_names)
}
