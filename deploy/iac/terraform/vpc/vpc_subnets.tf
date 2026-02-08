# ========================================================================
# VPC SUBNETS
# Public, Private App, and Private Data subnets
# ========================================================================

# ========================================================================
# PUBLIC SUBNETS
# ========================================================================
resource "aws_subnet" "public" {
  count = length(var.vpc_config.public_subnets)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.vpc_config.public_subnets[count.index].cidr
  availability_zone       = var.vpc_config.public_subnets[count.index].az
  map_public_ip_on_launch = true

  tags = merge(
    local.vpc_tags,
    {
      Name                                                                     = join("-", [var.environment, "public", "subnet", count.index + 1])
      "kubernetes.io/role/elb"                                                 = "1"  # For AWS Load Balancer Controller
      "kubernetes.io/cluster/${var.environment}-${var.project_name}-cluster" = "shared"  # EKS cluster tag
      Type                                                                     = "public"
    }
  )
}

# ========================================================================
# PRIVATE APP SUBNETS (EKS Nodes)
# ========================================================================
resource "aws_subnet" "private_app" {
  count = length(var.vpc_config.private_app_subnets)

  vpc_id            = aws_vpc.main.id
  cidr_block        = var.vpc_config.private_app_subnets[count.index].cidr
  availability_zone = var.vpc_config.private_app_subnets[count.index].az

  tags = merge(
    local.vpc_tags,
    {
      Name                                                                     = join("-", [var.environment, "private-app", "subnet", count.index + 1])
      "kubernetes.io/role/internal-elb"                                        = "1"  # For AWS Load Balancer Controller
      "kubernetes.io/cluster/${var.environment}-${var.project_name}-cluster" = "shared"  # EKS cluster tag
      Type                                                                     = "private-app"
    }
  )
}

# ========================================================================
# PRIVATE DATA SUBNETS (RDS, ElastiCache)
# ========================================================================
resource "aws_subnet" "private_data" {
  count = length(var.vpc_config.private_data_subnets)

  vpc_id            = aws_vpc.main.id
  cidr_block        = var.vpc_config.private_data_subnets[count.index].cidr
  availability_zone = var.vpc_config.private_data_subnets[count.index].az

  tags = merge(
    local.vpc_tags,
    {
      Name = join("-", [var.environment, "private-data", "subnet", count.index + 1])
      Type = "private-data"
    }
  )
}
