# ========================================================================
# EBS CSI DRIVER - IRSA ROLE
# Required for the EBS CSI addon to create/attach/detach EBS volumes.
# Created within the EKS module to avoid circular dependency with iam-roles.
# ========================================================================

resource "aws_iam_role" "ebs_csi_driver" {
  name = join("-", [var.environment, var.project_name, "ebs-csi-driver-irsa-role"])

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.cluster.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${replace(aws_iam_openid_connect_provider.cluster.url, "https://", "")}:sub" = "system:serviceaccount:kube-system:ebs-csi-controller-sa"
            "${replace(aws_iam_openid_connect_provider.cluster.url, "https://", "")}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = merge(
    var.common_tags,
    {
      Name      = join("-", [var.environment, var.project_name, "ebs-csi-driver-irsa-role"])
      Service   = "ebs-csi-driver"
      Namespace = "kube-system"
    }
  )
}

resource "aws_iam_role_policy_attachment" "ebs_csi_driver" {
  role       = aws_iam_role.ebs_csi_driver.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
}
