# ========================================================================
# EKS MODULE - OUTPUTS
# ========================================================================

output "eks_cluster" {
  description = "EKS cluster details"
  value = {
    id                     = aws_eks_cluster.main.id
    arn                    = aws_eks_cluster.main.arn
    name                   = aws_eks_cluster.main.name
    endpoint               = aws_eks_cluster.main.endpoint
    version                = aws_eks_cluster.main.version
    platform_version       = aws_eks_cluster.main.platform_version
    certificate_authority  = aws_eks_cluster.main.certificate_authority[0].data
  }
}

output "eks_oidc_provider" {
  description = "EKS OIDC provider details"
  value = {
    arn = aws_iam_openid_connect_provider.cluster.arn
    url = aws_iam_openid_connect_provider.cluster.url
  }
}

output "eks_node_groups" {
  description = "EKS node group details"
  value = {
    system = {
      id     = aws_eks_node_group.system.id
      arn    = aws_eks_node_group.system.arn
      status = aws_eks_node_group.system.status
    }
    app = {
      id     = aws_eks_node_group.application.id
      arn    = aws_eks_node_group.application.arn
      status = aws_eks_node_group.application.status
    }
    ai = var.eks_config.ai_node_group.enabled ? {
      id     = aws_eks_node_group.ai[0].id
      arn    = aws_eks_node_group.ai[0].arn
      status = aws_eks_node_group.ai[0].status
    } : null
  }
}

output "eks_cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
}

# Kubeconfig command
output "kubeconfig_command" {
  description = "Command to update kubeconfig"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name}"
}
