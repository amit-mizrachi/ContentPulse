# ========================================================================
# VPC MODULE - OUTPUTS
# ========================================================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "vpc_public_subnets" {
  description = "Public subnet information"
  value = [
    for subnet in aws_subnet.public : {
      id                = subnet.id
      cidr_block        = subnet.cidr_block
      availability_zone = subnet.availability_zone
    }
  ]
}

output "vpc_private_app_subnets" {
  description = "Private app subnet information"
  value = [
    for subnet in aws_subnet.private_app : {
      id                = subnet.id
      cidr_block        = subnet.cidr_block
      availability_zone = subnet.availability_zone
    }
  ]
}

output "vpc_private_data_subnets" {
  description = "Private data subnet information"
  value = [
    for subnet in aws_subnet.private_data : {
      id                = subnet.id
      cidr_block        = subnet.cidr_block
      availability_zone = subnet.availability_zone
    }
  ]
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "nat_gateway_ids" {
  description = "IDs of NAT Gateways"
  value       = aws_nat_gateway.main[*].id
}

output "vpc_endpoint_s3_id" {
  description = "ID of S3 VPC Endpoint"
  value       = length(aws_vpc_endpoint.s3) > 0 ? aws_vpc_endpoint.s3[0].id : null
}

output "vpc_endpoint_interface_ids" {
  description = "IDs of Interface VPC Endpoints"
  value = {
    for key, endpoint in aws_vpc_endpoint.interface : key => endpoint.id
  }
}

output "vpc_endpoints_security_group_id" {
  description = "Security group ID for VPC endpoints"
  value       = aws_security_group.vpc_endpoints.id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_app_route_table_ids" {
  description = "List of private app route table IDs"
  value       = aws_route_table.private_app[*].id
}

output "private_data_route_table_id" {
  description = "Private data route table ID"
  value       = aws_route_table.private_data.id
}
