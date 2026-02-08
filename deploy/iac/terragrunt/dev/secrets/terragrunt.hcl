# ========================================================================
# SECRETS MODULE - TERRAGRUNT WRAPPER
# Dependency Group 4: Secrets (depends on: rds)
# ========================================================================

include "root" {
  path   = find_in_parent_folders("root.hcl")
  expose = true
}

dependency "rds" {
  config_path = "../rds"

  mock_outputs = {
    db_credentials = {
      username = "admin"
      password = "mock-password-placeholder"
      host     = "mock-rds-endpoint.ap-south-1.rds.amazonaws.com"
      port     = 3306
      database = "llm_judge"
    }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

terraform {
  source = "${include.root.locals.repo_root}/deploy/iac/terraform/secrets"
}

inputs = {
  # Core variables
  aws_account_id      = include.root.inputs.aws_account_id
  aws_region          = include.root.inputs.aws_region
  environment         = include.root.inputs.environment
  project_name        = include.root.inputs.project_name

  # Secrets configuration
  secrets_config = include.root.inputs.secrets_config

  # RDS credentials from RDS module output
  rds_credentials = dependency.rds.outputs.db_credentials

  # Common tags
  common_tags = include.root.inputs.common_tags
}
