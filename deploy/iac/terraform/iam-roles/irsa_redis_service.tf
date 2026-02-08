# ========================================================================
# IRSA - REDIS SERVICE
# Permissions: AppConfig read access
# ========================================================================

resource "aws_iam_role" "redis_service_irsa" {
  count = local.create_irsa ? 1 : 0

  name = "${var.environment}-redis-service-irsa-role"

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
            "${local.oidc_provider_id}:sub" = "system:serviceaccount:llm-judge:redis-service"
            "${local.oidc_provider_id}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = merge(local.iam_tags, {
    Name      = "${var.environment}-redis-service-irsa-role"
    Service   = "redis-service"
    Namespace = "llm-judge"
  })
}

resource "aws_iam_policy" "redis_service_policy" {
  count = local.create_irsa ? 1 : 0

  name        = "${var.environment}-redis-service-policy"
  description = "IAM policy for redis-service in llm-judge namespace"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["appconfig:GetLatestConfiguration", "appconfig:StartConfigurationSession"]
        Resource = ["*"]
      }
    ]
  })

  tags = merge(local.iam_tags, {
    Name      = "${var.environment}-redis-service-policy"
    Service   = "redis-service"
    Namespace = "llm-judge"
  })
}

resource "aws_iam_role_policy_attachment" "redis_service_attachment" {
  count = local.create_irsa ? 1 : 0

  role       = aws_iam_role.redis_service_irsa[0].name
  policy_arn = aws_iam_policy.redis_service_policy[0].arn
}
