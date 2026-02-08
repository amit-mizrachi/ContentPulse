# ========================================================================
# IRSA - PERSISTENCE SERVICE
# Permissions: Secrets Manager (RDS credentials), AppConfig read access
# ========================================================================

resource "aws_iam_role" "persistence_service_irsa" {
  count = local.create_irsa ? 1 : 0

  name = "${var.environment}-persistence-service-irsa-role"

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
            "${local.oidc_provider_id}:sub" = "system:serviceaccount:llm-judge:persistence-service"
            "${local.oidc_provider_id}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = merge(local.iam_tags, {
    Name      = "${var.environment}-persistence-service-irsa-role"
    Service   = "persistence-service"
    Namespace = "llm-judge"
  })
}

resource "aws_iam_policy" "persistence_service_policy" {
  count = local.create_irsa ? 1 : 0

  name        = "${var.environment}-persistence-service-policy"
  description = "IAM policy for persistence-service in llm-judge namespace"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [var.secret_arns["rds_credentials"]]
      },
      {
        Effect   = "Allow"
        Action   = ["appconfig:GetLatestConfiguration", "appconfig:StartConfigurationSession"]
        Resource = ["*"]
      }
    ]
  })

  tags = merge(local.iam_tags, {
    Name      = "${var.environment}-persistence-service-policy"
    Service   = "persistence-service"
    Namespace = "llm-judge"
  })
}

resource "aws_iam_role_policy_attachment" "persistence_service_attachment" {
  count = local.create_irsa ? 1 : 0

  role       = aws_iam_role.persistence_service_irsa[0].name
  policy_arn = aws_iam_policy.persistence_service_policy[0].arn
}
