# ========================================================================
# IRSA - GATEWAY SERVICE
# Permissions: Publish to SNS inference topic
# ========================================================================

resource "aws_iam_role" "gateway_service_irsa" {
  count = local.create_irsa ? 1 : 0

  name = "${var.environment}-gateway-service-irsa-role"

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
            "${local.oidc_provider_id}:sub" = "system:serviceaccount:llm-judge:gateway-service"
            "${local.oidc_provider_id}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = merge(local.iam_tags, {
    Name      = "${var.environment}-gateway-service-irsa-role"
    Service   = "gateway-service"
    Namespace = "llm-judge"
  })
}

resource "aws_iam_policy" "gateway_service_policy" {
  count = local.create_irsa ? 1 : 0

  name        = "${var.environment}-gateway-service-policy"
  description = "IAM policy for gateway-service in llm-judge namespace"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = [var.sns_topic_arns["inference"]]
      }
    ]
  })

  tags = merge(local.iam_tags, {
    Name      = "${var.environment}-gateway-service-policy"
    Service   = "gateway-service"
    Namespace = "llm-judge"
  })
}

resource "aws_iam_role_policy_attachment" "gateway_service_attachment" {
  count = local.create_irsa ? 1 : 0

  role       = aws_iam_role.gateway_service_irsa[0].name
  policy_arn = aws_iam_policy.gateway_service_policy[0].arn
}
