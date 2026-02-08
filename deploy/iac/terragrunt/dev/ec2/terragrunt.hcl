# ========================================================================
# EC2 MODULE - TERRAGRUNT WRAPPER
# Dependency Group 2: Network/Identity (depends on VPC, IAM, Security Groups)
# ========================================================================

include "root" {
  path   = find_in_parent_folders("root.hcl")
  expose = true
}

# ========================================================================
# DEPENDENCIES
# ========================================================================
dependency "vpc" {
  config_path = "../vpc"

  mock_outputs = {
    vpc_id = "vpc-mock123456"
    vpc_public_subnets = [
      {
        id                = "subnet-mock-public-1"
        cidr_block        = "10.0.1.0/24"
        availability_zone = "us-east-1a"
      }
    ]
    private_app_route_table_ids = ["rtb-mock-app-1", "rtb-mock-app-2", "rtb-mock-app-3"]
    private_data_route_table_id = "rtb-mock-data"
  }

  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "iam_roles" {
  config_path = "../iam-roles"

  mock_outputs = {
    ec2_iam_instance_profiles = {
      "nat-router" = {
        arn  = "arn:aws:iam::123456789012:instance-profile/mock-nat-router-profile"
        id   = "mock-nat-router-profile"
        name = "dev-nadav-nat-router-instance-profile"
      }
    }
  }

  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "security_groups" {
  config_path = "../security-groups"

  mock_outputs = {
    nat_instance_security_group = {
      id   = "sg-mock123456"
      name = "dev-nadav-passive-on-nat-instance-sg"
      arn  = "arn:aws:ec2:us-east-1:123456789012:security-group/sg-mock123456"
    }
  }

  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

# ========================================================================
# TERRAFORM SOURCE
# ========================================================================
terraform {
  source = "${include.root.locals.repo_root}/deploy/iac/terraform/ec2"
}

# ========================================================================
# MODULE INPUTS
# ========================================================================
inputs = {
  # Core variables
  aws_account_id     = include.root.inputs.aws_account_id
  aws_region         = include.root.inputs.aws_region
  environment         = include.root.inputs.environment

  # EC2 configuration
  ec2_config = include.root.inputs.ec2_config

  # VPC dependencies
  vpc_public_subnets = dependency.vpc.outputs.vpc_public_subnets

  # Build map of route table IDs for private subnets
  vpc_private_route_table_ids = merge(
    {
      for idx, rtb_id in dependency.vpc.outputs.private_app_route_table_ids :
      "app-${idx}" => rtb_id
    },
    {
      "data" = dependency.vpc.outputs.private_data_route_table_id
    }
  )

  # IAM dependencies
  iam_nat_router_instance_profile = dependency.iam_roles.outputs.ec2_iam_instance_profiles["nat-router"]

  # Security group dependencies
  sg_nat_security_group_ids = [dependency.security_groups.outputs.nat_instance_security_group.id]
}
