# ========================================================================
# EKS CLUSTER
# ========================================================================

resource "aws_eks_cluster" "main" {
  name     = var.eks_config.cluster_name
  role_arn = aws_iam_role.cluster.arn
  version  = var.eks_config.cluster_version

  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_private_access = var.eks_config.endpoint_private_access
    endpoint_public_access  = var.eks_config.endpoint_public_access
    security_group_ids      = [var.eks_nodes_security_group_id]
  }

  enabled_cluster_log_types = var.eks_config.cluster_logging

  tags = merge(
    var.common_tags,
    {
      Name = var.eks_config.cluster_name
    }
  )

  depends_on = [
    aws_iam_role_policy_attachment.cluster_policy,
    aws_iam_role_policy_attachment.cluster_vpc_resource_controller
  ]
}
