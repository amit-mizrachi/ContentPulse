# ========================================================================
# MARKER SECURITY GROUP - NAT INSTANCE
# Note: This includes ingress/egress rules as NAT needs bidirectional traffic
# ========================================================================

locals {
  marker_nat_instance_sg_name = join("-", [var.environment, "marker-nat-instance-sg"])
}

resource "aws_security_group" "nat_instance" {
  name        = local.marker_nat_instance_sg_name
  description = "Marker security group for NAT instance (used as source/target in other SG rules)"
  vpc_id      = var.vpc_id

  tags = merge(
    local.sg_tags,
    {
      Name = local.marker_nat_instance_sg_name
    }
  )
}

# Ingress: Allow all traffic from VPC CIDR
resource "aws_vpc_security_group_ingress_rule" "nat_instance_from_vpc" {
  security_group_id = aws_security_group.nat_instance.id
  description       = "Allow all traffic from VPC CIDR"
  from_port         = -1
  to_port           = -1
  ip_protocol       = "-1"
  cidr_ipv4         = var.vpc_cidr_block

  tags = merge(
    local.sg_tags,
    {
      Name = "nat-instance-vpc-ingress"
    }
  )
}

# Egress: Allow all outbound traffic
resource "aws_vpc_security_group_egress_rule" "nat_instance_to_internet" {
  security_group_id = aws_security_group.nat_instance.id
  description       = "Allow all outbound traffic to internet"
  from_port         = -1
  to_port           = -1
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"

  tags = merge(
    local.sg_tags,
    {
      Name = "nat-instance-internet-egress"
    }
  )
}
