locals {
  nat_router_prefix     = join("-", [var.environment, "nat-router"])
  nat_router_eip_prefix = join("-", [var.environment, "nat-router-eip"])
}

# fck-nat AMI lookup (ARM64 for Graviton instances)
data "aws_ami" "fck_nat" {
  most_recent = true
  owners      = ["568608671756"]  # fck-nat official AWS account

  filter {
    name   = "name"
    values = ["fck-nat-al2023-*-arm64-*"]
  }

  filter {
    name   = "architecture"
    values = ["arm64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}
