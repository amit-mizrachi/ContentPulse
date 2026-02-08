# ========================================================================
# RDS SUBNET GROUP
# Defines which subnets the RDS instance can be deployed in
# ========================================================================

resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = var.subnet_ids

  tags = merge(local.rds_tags, {
    Name = "${local.name_prefix}-db-subnet-group"
  })
}
