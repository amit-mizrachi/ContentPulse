# ========================================================================
# EKS ADDONS
# ========================================================================

resource "aws_eks_addon" "vpc_cni" {
  cluster_name                = aws_eks_cluster.main.name
  addon_name                  = "vpc-cni"
  addon_version               = var.eks_config.addons.vpc_cni.version
  configuration_values        = var.eks_config.addons.vpc_cni.configuration_values
  resolve_conflicts_on_create = "OVERWRITE"

  tags = merge(
    var.common_tags,
    {
      Name = "vpc-cni"
    }
  )
}

resource "aws_eks_addon" "coredns" {
  cluster_name                = aws_eks_cluster.main.name
  addon_name                  = "coredns"
  addon_version               = var.eks_config.addons.coredns.version
  resolve_conflicts_on_create = "OVERWRITE"

  tags = merge(
    var.common_tags,
    {
      Name = "coredns"
    }
  )

  depends_on = [aws_eks_node_group.system]
}

resource "aws_eks_addon" "kube_proxy" {
  cluster_name                = aws_eks_cluster.main.name
  addon_name                  = "kube-proxy"
  addon_version               = var.eks_config.addons.kube_proxy.version
  resolve_conflicts_on_create = "OVERWRITE"

  tags = merge(
    var.common_tags,
    {
      Name = "kube-proxy"
    }
  )
}

resource "aws_eks_addon" "ebs_csi_driver" {
  cluster_name                = aws_eks_cluster.main.name
  addon_name                  = "aws-ebs-csi-driver"
  addon_version               = var.eks_config.addons.ebs_csi_driver.version
  resolve_conflicts_on_create = "OVERWRITE"

  tags = merge(
    var.common_tags,
    {
      Name = "ebs-csi-driver"
    }
  )
}
