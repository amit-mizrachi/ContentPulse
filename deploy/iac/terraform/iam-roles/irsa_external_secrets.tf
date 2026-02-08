# ========================================================================
# IRSA - EXTERNAL SECRETS OPERATOR
# Permissions: Secrets Manager access for all project secrets
# ========================================================================

resource "aws_iam_role" "external_secrets_irsa" {
  count = local.create_irsa ? 1 : 0

  name = "${var.environment}-external-secrets-irsa-role"

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
            "${local.oidc_provider_id}:sub" = "system:serviceaccount:external-secrets-system:external-secrets"
            "${local.oidc_provider_id}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = merge(local.iam_tags, {
    Name      = "${var.environment}-external-secrets-irsa-role"
    Service   = "external-secrets"
    Namespace = "external-secrets-system"
  })
}

resource "aws_iam_policy" "external_secrets_policy" {
  count = local.create_irsa ? 1 : 0

  name        = "${var.environment}-external-secrets-policy"
  description = "IAM policy for external-secrets in external-secrets-system namespace"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:${var.environment}/${var.project_name}/*"
        ]
      }
    ]
  })

  tags = merge(local.iam_tags, {
    Name      = "${var.environment}-external-secrets-policy"
    Service   = "external-secrets"
    Namespace = "external-secrets-system"
  })
}

resource "aws_iam_role_policy_attachment" "external_secrets_attachment" {
  count = local.create_irsa ? 1 : 0

  role       = aws_iam_role.external_secrets_irsa[0].name
  policy_arn = aws_iam_policy.external_secrets_policy[0].arn
}
