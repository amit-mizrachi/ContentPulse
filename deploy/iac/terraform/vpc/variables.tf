# ========================================================================
# VPC MODULE - INPUT VARIABLES
# ========================================================================

# Core Norman Variables (required in every module)
variable "aws_account_id" {
  type        = string
  description = "AWS Account ID"
}

variable "aws_region" {
  type        = string
  description = "AWS Region"
}

variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"
}

variable "project_name" {
  type        = string
  description = "Project name"
}

# VPC Configuration
variable "vpc_config" {
  type = object({
    cidr_block           = string
    enable_dns_hostnames = bool
    enable_dns_support   = bool
    availability_zones   = list(string)

    public_subnets = list(object({
      cidr = string
      az   = string
    }))

    private_app_subnets = list(object({
      cidr = string
      az   = string
    }))

    private_data_subnets = list(object({
      cidr = string
      az   = string
    }))

    vpc_endpoints = list(string)

    enable_nat_gateway = bool
    single_nat_gateway = bool
  })
  description = "VPC configuration object"
}

variable "common_tags" {
  type        = map(string)
  description = "Common tags to apply to all resources"
  default     = {}
}
