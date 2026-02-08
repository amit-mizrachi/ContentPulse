# ========================================================================
# VPC ROUTE TABLES
# Route tables and subnet associations
# ========================================================================

# ========================================================================
# PUBLIC ROUTE TABLE
# ========================================================================
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.vpc_tags,
    {
      Name = join("-", [var.environment, "public", "route-table"])
    }
  )
}

# Public Route to Internet Gateway
resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

# Public Subnet Route Table Associations
resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# ========================================================================
# PRIVATE APP ROUTE TABLE
# ========================================================================
resource "aws_route_table" "private_app" {
  count = var.vpc_config.single_nat_gateway ? 1 : length(var.vpc_config.private_app_subnets)

  vpc_id = aws_vpc.main.id

  tags = merge(
    local.vpc_tags,
    {
      Name = join("-", [
        var.environment,
        "private-app",
        "route-table",
        var.vpc_config.single_nat_gateway ? "shared" : tostring(count.index + 1)
      ])
    }
  )
}

# Private App Route Table Associations
resource "aws_route_table_association" "private_app" {
  count = length(aws_subnet.private_app)

  subnet_id      = aws_subnet.private_app[count.index].id
  route_table_id = var.vpc_config.single_nat_gateway ? aws_route_table.private_app[0].id : aws_route_table.private_app[count.index].id
}

# ========================================================================
# PRIVATE DATA ROUTE TABLE
# ========================================================================
resource "aws_route_table" "private_data" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.vpc_tags,
    {
      Name = join("-", [var.environment, "private-data", "route-table"])
    }
  )
}

# Private Data Route Table Associations
resource "aws_route_table_association" "private_data" {
  count = length(aws_subnet.private_data)

  subnet_id      = aws_subnet.private_data[count.index].id
  route_table_id = aws_route_table.private_data.id
}
