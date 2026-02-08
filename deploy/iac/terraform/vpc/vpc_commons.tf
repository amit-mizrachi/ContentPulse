# ========================================================================
# VPC MODULE - COMMONS
# VPC resource, Internet Gateway, and shared locals
# ========================================================================

locals {
  vpc_name = join("-", [var.environment, var.project_name, "vpc"])

  # Common tags for all VPC resources
  vpc_tags = var.common_tags
}

# ========================================================================
# VPC
# ========================================================================
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_config.cidr_block
  enable_dns_hostnames = var.vpc_config.enable_dns_hostnames
  enable_dns_support   = var.vpc_config.enable_dns_support

  tags = merge(
    local.vpc_tags,
    {
      Name = local.vpc_name
    }
  )
}

# ========================================================================
# INTERNET GATEWAY
# ========================================================================
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.vpc_tags,
    {
      Name = join("-", [var.environment, var.project_name, "igw"])
    }
  )
}
