# ========================================================================
# NAT ROUTER INSTANCES
# Uses fck-nat for cost-effective NAT functionality (~$3/month vs $32/month)
# ========================================================================

resource "aws_instance" "nat_routers" {
  ami                    = data.aws_ami.fck_nat.id
  instance_type          = var.ec2_config.nat.instance_type
  iam_instance_profile   = var.iam_nat_router_instance_profile.name
  subnet_id              = var.vpc_public_subnets[0].id  # Deploy in first public subnet
  source_dest_check      = false
  vpc_security_group_ids = var.sg_nat_security_group_ids

  root_block_device {
    volume_size           = var.ec2_config.nat.volume_size
    volume_type           = var.ec2_config.nat.volume_type
    delete_on_termination = var.ec2_config.nat.delete_on_termination
    encrypted             = true

    tags = {
      Name               = join("-", [local.nat_router_prefix, "root-volume"])
    }
  }

  # User data for fck-nat configuration
  user_data = <<-EOF
              #!/bin/bash
              # fck-nat AMI auto-configures NAT functionality
              echo "NAT instance initialized for ${var.environment}"
              EOF

  monitoring = true

  tags = {
    Name               = local.nat_router_prefix
  }

  lifecycle {
    ignore_changes = [ami]  # Prevent recreation when AMI updates
  }
}

# ========================================================================
# ELASTIC IPS FOR NAT ROUTERS
# ========================================================================
resource "aws_eip" "nat_elastic_ips" {
  instance = aws_instance.nat_routers.id
  domain   = "vpc"

  tags = {
    Name               = join("-", [local.nat_router_eip_prefix])
  }

  lifecycle {
    prevent_destroy = false
  }
}

# ========================================================================
# ROUTE TABLE UPDATES (Private Subnets -> NAT Instance)
# ========================================================================
resource "aws_route" "route_table_forward_to_nat" {
  for_each = var.vpc_private_route_table_ids

  destination_cidr_block = "0.0.0.0/0"
  network_interface_id   = aws_instance.nat_routers.primary_network_interface_id
  route_table_id         = each.value
}
