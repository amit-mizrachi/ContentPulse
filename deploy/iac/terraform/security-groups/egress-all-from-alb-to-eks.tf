# ========================================================================
# EGRESS - ALL TRAFFIC FROM ALB TO EKS NODES
# ========================================================================

# Egress: All traffic from ALB to EKS nodes
resource "aws_vpc_security_group_egress_rule" "alb_to_eks" {
  security_group_id            = aws_security_group.alb.id
  description                  = "Allow all traffic from ALB to EKS nodes"
  ip_protocol                  = "-1"
  referenced_security_group_id = aws_security_group.eks_nodes.id

  tags = merge(
    local.sg_tags,
    {
      Name = "alb-to-eks-egress"
    }
  )
}
