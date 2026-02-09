# ========================================================================
# SECURITY GROUPS MODULE - OUTPUTS
# ========================================================================

output "alb_security_group" {
  description = "ALB security group details"
  value = {
    id   = aws_security_group.alb.id
    name = aws_security_group.alb.name
    arn  = aws_security_group.alb.arn
  }
}

output "eks_nodes_security_group" {
  description = "EKS nodes security group details"
  value = {
    id   = aws_security_group.eks_nodes.id
    name = aws_security_group.eks_nodes.name
    arn  = aws_security_group.eks_nodes.arn
  }
}

# RDS security group removed - simple_sport_news uses MongoDB Atlas (no MySQL)

output "nat_instance_security_group" {
  description = "NAT instance security group details"
  value = {
    id   = aws_security_group.nat_instance.id
    name = aws_security_group.nat_instance.name
    arn  = aws_security_group.nat_instance.arn
  }
}
