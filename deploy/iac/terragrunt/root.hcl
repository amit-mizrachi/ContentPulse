# ========================================================================
# IAC - ROOT CONFIGURATION
# Provider Generation + Remote State Configuration
# ========================================================================

locals {
  # Load global configuration
  configurations = read_terragrunt_config(find_in_parent_folders("configuration.hcl"))
  repo_root      = get_repo_root()

  # Extract commonly used values
  aws_region          = local.configurations.locals.aws_region
  aws_account_id      = local.configurations.locals.aws_account_id
  environment = local.configurations.locals.environment
  project_name        = local.configurations.locals.project_name
}

# ========================================================================
# AWS PROVIDER GENERATION
# ========================================================================
generate "aws_provider" {
  path      = "aws_provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  required_version = ">= 1.10.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "${local.aws_region}"

  default_tags {
    tags = {
      Project     = "${local.project_name}"
      Environment = "${local.environment}"
      ManagedBy   = "terraform"
    }
  }
}
EOF
}

# ========================================================================
# REMOTE STATE CONFIGURATION (S3 Native Locking)
# ========================================================================
# Note: Using S3 native state locking (use_lockfile) instead of DynamoDB.
# Requires Terraform >= 1.10.0. Uses S3 Conditional Writes for atomic locking.
# ========================================================================
remote_state {
  backend = "s3"

  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }

  config = {
    bucket       = "${local.environment}-${local.project_name}-terraform-state"
    key          = "${path_relative_to_include()}/terraform.tfstate"
    region       = local.aws_region
    encrypt      = true
    use_lockfile = true  # S3 native locking - replaces DynamoDB table

    # S3 bucket tags
    s3_bucket_tags = {
      Name        = "${local.environment}-${local.project_name}-terraform-state"
      Project     = local.project_name
      Environment = local.environment
      ManagedBy   = "terraform"
    }
  }
}

# ========================================================================
# GLOBAL INPUTS (Passed to all modules)
# ========================================================================
inputs = merge(
  local.configurations.locals,
  {
    # Expose repo_root for module source paths
    repo_root = local.repo_root
  }
)

# ========================================================================
# TERRAFORM SETTINGS
# ========================================================================
terraform {
  extra_arguments "retry_lock" {
    commands = [
      "init",
      "apply",
      "refresh",
      "import",
      "plan",
      "taint",
      "untaint"
    ]

    arguments = [
      "-lock-timeout=20m"
    ]
  }

  extra_arguments "disable_input" {
    commands  = get_terraform_commands_that_need_input()
    arguments = ["-input=false"]
  }
}
