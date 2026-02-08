# ========================================================================
# VPC ENDPOINTS (Interface & Gateway)
# ========================================================================

# Security Group for VPC Endpoints
resource "aws_security_group" "vpc_endpoints" {
  name        = join("-", [var.environment, "passive-on-vpc-endpoints-sg"])
  description = "Security group for VPC endpoints"
  vpc_id      = aws_vpc.main.id

  tags = merge(
    local.vpc_tags,
    {
      Name = join("-", [var.environment, "passive-on-vpc-endpoints-sg"])
    }
  )
}

# Ingress rule for VPC Endpoints
resource "aws_vpc_security_group_ingress_rule" "vpc_endpoints_https" {
  security_group_id = aws_security_group.vpc_endpoints.id
  description       = "Allow HTTPS from VPC CIDR"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  cidr_ipv4         = aws_vpc.main.cidr_block

  tags = merge(
    local.vpc_tags,
    {
      Name = "vpc-endpoints-https-ingress"
    }
  )
}

# ========================================================================
# S3 GATEWAY ENDPOINT
# ========================================================================
resource "aws_vpc_endpoint" "s3" {
  count = contains(var.vpc_config.vpc_endpoints, "s3") ? 1 : 0

  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"

  route_table_ids = concat(
    [aws_route_table.public.id],
    aws_route_table.private_app[*].id,
    [aws_route_table.private_data.id]
  )

  tags = merge(
    local.vpc_tags,
    {
      Name = join("-", [var.environment, "s3", "endpoint"])
    }
  )
}

# ========================================================================
# INTERFACE VPC ENDPOINTS
# ========================================================================
locals {
  interface_endpoints = {
    for service in var.vpc_config.vpc_endpoints :
    service => service if service != "s3"
  }
}

resource "aws_vpc_endpoint" "interface" {
  for_each = local.interface_endpoints

  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.${each.value}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private_app[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = merge(
    local.vpc_tags,
    {
      Name = join("-", [var.environment, each.key, "endpoint"])
    }
  )
}
