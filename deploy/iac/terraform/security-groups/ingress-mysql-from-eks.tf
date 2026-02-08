# ========================================================================
# INGRESS - MYSQL FROM EKS NODES TO RDS
# ========================================================================

locals {
  ingress_mysql_from_eks_group_name = join("-", [var.environment, "ingress-mysql-from-eks-sg"])
}

resource "aws_security_group" "rds" {
  name        = local.ingress_mysql_from_eks_group_name
  description = "Allow MySQL inbound traffic from EKS nodes"
  vpc_id      = var.vpc_id

  tags = merge(
    local.sg_tags,
    {
      Name = local.ingress_mysql_from_eks_group_name
    }
  )
}

# Ingress: MySQL from EKS nodes
resource "aws_vpc_security_group_ingress_rule" "rds_mysql_from_eks" {
  security_group_id            = aws_security_group.rds.id
  description                  = "Allow MySQL from EKS nodes"
  from_port                    = 3306
  to_port                      = 3306
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.eks_nodes.id

  tags = merge(
    local.sg_tags,
    {
      Name = "rds-mysql-from-eks-ingress"
    }
  )
}
