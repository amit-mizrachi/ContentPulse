# ========================================================================
# EKS MODULE - TERRAGRUNT WRAPPER
# Dependency Group 5: Compute Layer (depends on: vpc, security-groups)
# ========================================================================

include "root" {
  path   = find_in_parent_folders("root.hcl")
  expose = true
}

dependency "vpc" {
  config_path = "../vpc"

  mock_outputs = {
    vpc_id = "vpc-mock123456"
    vpc_private_app_subnets = [
      { id = "subnet-mock1", cidr_block = "10.0.16.0/20", availability_zone = "us-east-1a" },
      { id = "subnet-mock2", cidr_block = "10.0.32.0/20", availability_zone = "us-east-1b" },
      { id = "subnet-mock3", cidr_block = "10.0.48.0/20", availability_zone = "us-east-1c" }
    ]
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "security_groups" {
  config_path = "../security-groups"

  mock_outputs = {
    eks_nodes_security_group = {
      id   = "sg-mock123456"
      name = "mock-eks-nodes-sg"
      arn  = "arn:aws:ec2:us-east-1:123456789012:security-group/sg-mock123456"
    }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

terraform {
  source = "${include.root.locals.repo_root}/deploy/iac/terraform/eks"
}

inputs = {
  # Core variables
  aws_account_id = include.root.inputs.aws_account_id
  aws_region     = include.root.inputs.aws_region
  environment    = include.root.inputs.environment
  project_name   = include.root.inputs.project_name

  # EKS configuration
  eks_config = include.root.inputs.eks_config

  # Dependencies
  vpc_id                      = dependency.vpc.outputs.vpc_id
  subnet_ids                  = [for s in dependency.vpc.outputs.vpc_private_app_subnets : s.id]
  eks_nodes_security_group_id = dependency.security_groups.outputs.eks_nodes_security_group.id

  # Common tags
  common_tags = include.root.inputs.common_tags
}
