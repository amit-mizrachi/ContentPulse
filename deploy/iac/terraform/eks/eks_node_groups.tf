# ========================================================================
# EKS NODE GROUPS
# ========================================================================

# ========================================================================
# SYSTEM NODE GROUP
# ========================================================================
resource "aws_eks_node_group" "system" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = join("-", [var.environment, var.eks_config.system_node_group.name, "ng"])
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = var.subnet_ids

  capacity_type  = var.eks_config.system_node_group.capacity_type
  instance_types = var.eks_config.system_node_group.instance_types
  disk_size      = var.eks_config.system_node_group.disk_size

  scaling_config {
    desired_size = var.eks_config.system_node_group.desired_size
    min_size     = var.eks_config.system_node_group.min_size
    max_size     = var.eks_config.system_node_group.max_size
  }

  labels = var.eks_config.system_node_group.labels

  tags = merge(
    var.common_tags,
    {
      Name = join("-", [var.environment, var.eks_config.system_node_group.name, "ng"])
      Type = "system"
    }
  )

  depends_on = [
    aws_iam_role_policy_attachment.node_worker_policy,
    aws_iam_role_policy_attachment.node_cni_policy,
    aws_iam_role_policy_attachment.node_registry_policy
  ]
}

# ========================================================================
# APPLICATION NODE GROUP
# ========================================================================
resource "aws_eks_node_group" "application" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = join("-", [var.environment, var.eks_config.app_node_group.name, "ng"])
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = var.subnet_ids

  capacity_type  = var.eks_config.app_node_group.capacity_type
  instance_types = var.eks_config.app_node_group.instance_types
  disk_size      = var.eks_config.app_node_group.disk_size

  scaling_config {
    desired_size = var.eks_config.app_node_group.desired_size
    min_size     = var.eks_config.app_node_group.min_size
    max_size     = var.eks_config.app_node_group.max_size
  }

  labels = var.eks_config.app_node_group.labels

  tags = merge(
    var.common_tags,
    {
      Name = join("-", [var.environment, var.eks_config.app_node_group.name, "ng"])
      Type = "application"
    }
  )

  depends_on = [
    aws_iam_role_policy_attachment.node_worker_policy,
    aws_iam_role_policy_attachment.node_cni_policy,
    aws_iam_role_policy_attachment.node_registry_policy
  ]
}

# ========================================================================
# AI/GPU NODE GROUP (scales to 0 when idle)
# ========================================================================
resource "aws_eks_node_group" "ai" {
  count = var.eks_config.ai_node_group.enabled ? 1 : 0

  cluster_name    = aws_eks_cluster.main.name
  node_group_name = join("-", [var.environment, var.eks_config.ai_node_group.name, "ng"])
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = var.subnet_ids

  capacity_type  = var.eks_config.ai_node_group.capacity_type
  instance_types = var.eks_config.ai_node_group.instance_types
  disk_size      = var.eks_config.ai_node_group.disk_size
  ami_type       = "AL2_x86_64_GPU"  # GPU-optimized AMI

  scaling_config {
    desired_size = var.eks_config.ai_node_group.desired_size
    min_size     = var.eks_config.ai_node_group.min_size
    max_size     = var.eks_config.ai_node_group.max_size
  }

  labels = var.eks_config.ai_node_group.labels

  dynamic "taint" {
    for_each = var.eks_config.ai_node_group.taints
    content {
      key    = taint.value.key
      value  = taint.value.value
      effect = taint.value.effect
    }
  }

  tags = merge(
    var.common_tags,
    {
      Name = join("-", [var.environment, var.eks_config.ai_node_group.name, "ng"])
      Type = "ai-gpu"
      "k8s.io/cluster-autoscaler/enabled"                        = "true"
      "k8s.io/cluster-autoscaler/${var.eks_config.cluster_name}" = "owned"
    }
  )

  depends_on = [
    aws_iam_role_policy_attachment.node_worker_policy,
    aws_iam_role_policy_attachment.node_cni_policy,
    aws_iam_role_policy_attachment.node_registry_policy
  ]
}
