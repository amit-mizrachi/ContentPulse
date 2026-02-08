# ========================================================================
# EGRESS - ALL TRAFFIC FROM EKS NODES
# ========================================================================

# Egress: All traffic from EKS nodes
resource "aws_vpc_security_group_egress_rule" "eks_nodes_all" {
  security_group_id = aws_security_group.eks_nodes.id
  description       = "Allow all outbound traffic from EKS nodes"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"

  tags = merge(
    local.sg_tags,
    {
      Name = "eks-nodes-all-egress"
    }
  )
}
