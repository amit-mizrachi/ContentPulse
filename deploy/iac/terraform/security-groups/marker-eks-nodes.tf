# ========================================================================
# MARKER SECURITY GROUP - EKS NODES
# Marker security group for EKS worker nodes (used as source/target in other SG rules)
# ========================================================================

locals {
  marker_eks_nodes_sg_name = join("-", [var.environment, "marker-eks-nodes-sg"])
}

resource "aws_security_group" "eks_nodes" {
  name        = local.marker_eks_nodes_sg_name
  description = "Marker security group for EKS worker nodes (used as source/target in other SG rules)"
  vpc_id      = var.vpc_id

  tags = merge(
    local.sg_tags,
    {
      Name = local.marker_eks_nodes_sg_name
      "kubernetes.io/cluster/${local.cluster_name}" = "owned"
    }
  )
}
