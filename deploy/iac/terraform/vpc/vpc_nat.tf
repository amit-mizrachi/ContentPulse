# ========================================================================
# VPC NAT GATEWAY (Optional - disabled by default, using NAT instance)
# ========================================================================

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count = var.vpc_config.enable_nat_gateway ? (var.vpc_config.single_nat_gateway ? 1 : length(var.vpc_config.availability_zones)) : 0

  domain = "vpc"

  tags = merge(
    local.vpc_tags,
    {
      Name = join("-", [var.environment, "nat", "eip", count.index + 1])
    }
  )

  depends_on = [aws_internet_gateway.main]
}

# NAT Gateways
resource "aws_nat_gateway" "main" {
  count = var.vpc_config.enable_nat_gateway ? (var.vpc_config.single_nat_gateway ? 1 : length(var.vpc_config.availability_zones)) : 0

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(
    local.vpc_tags,
    {
      Name = join("-", [var.environment, "nat", "gw", count.index + 1])
    }
  )

  depends_on = [aws_internet_gateway.main]
}

# NAT Gateway Routes for Private App Subnets
resource "aws_route" "private_app_nat" {
  count = var.vpc_config.enable_nat_gateway ? length(aws_route_table.private_app) : 0

  route_table_id         = aws_route_table.private_app[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = var.vpc_config.single_nat_gateway ? aws_nat_gateway.main[0].id : aws_nat_gateway.main[count.index].id
}
