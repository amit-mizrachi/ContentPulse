# ========================================================================
# IRSA - CLUSTER AUTOSCALER
# Permissions: AutoScaling and EC2 for node group scaling
# ========================================================================

resource "aws_iam_role" "cluster_autoscaler_irsa" {
  count = local.create_irsa ? 1 : 0

  name = "${var.environment}-cluster-autoscaler-irsa-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = var.eks_oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${local.oidc_provider_id}:sub" = "system:serviceaccount:kube-system:cluster-autoscaler"
            "${local.oidc_provider_id}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = merge(local.iam_tags, {
    Name      = "${var.environment}-cluster-autoscaler-irsa-role"
    Service   = "cluster-autoscaler"
    Namespace = "kube-system"
  })
}

resource "aws_iam_policy" "cluster_autoscaler_policy" {
  count = local.create_irsa ? 1 : 0

  name        = "${var.environment}-cluster-autoscaler-policy"
  description = "IAM policy for cluster-autoscaler in kube-system namespace"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "autoscaling:DescribeAutoScalingGroups",
          "autoscaling:DescribeAutoScalingInstances",
          "autoscaling:DescribeLaunchConfigurations",
          "autoscaling:DescribeScalingActivities",
          "autoscaling:DescribeTags",
          "ec2:DescribeImages",
          "ec2:DescribeInstanceTypes",
          "ec2:DescribeLaunchTemplateVersions",
          "ec2:GetInstanceTypesFromInstanceRequirements",
          "eks:DescribeNodegroup"
        ]
        Resource = ["*"]
      },
      {
        Effect = "Allow"
        Action = [
          "autoscaling:SetDesiredCapacity",
          "autoscaling:TerminateInstanceInAutoScalingGroup"
        ]
        Resource = ["*"]
      }
    ]
  })

  tags = merge(local.iam_tags, {
    Name      = "${var.environment}-cluster-autoscaler-policy"
    Service   = "cluster-autoscaler"
    Namespace = "kube-system"
  })
}

resource "aws_iam_role_policy_attachment" "cluster_autoscaler_attachment" {
  count = local.create_irsa ? 1 : 0

  role       = aws_iam_role.cluster_autoscaler_irsa[0].name
  policy_arn = aws_iam_policy.cluster_autoscaler_policy[0].arn
}
