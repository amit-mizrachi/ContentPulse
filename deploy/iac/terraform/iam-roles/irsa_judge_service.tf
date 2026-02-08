# ========================================================================
# IRSA - JUDGE SERVICE
# Permissions: SQS consume (judge queue)
# Note: No Secrets Manager access - users provide their own LLM API keys
# ========================================================================

resource "aws_iam_role" "judge_service_irsa" {
  count = local.create_irsa ? 1 : 0

  name = "${var.environment}-judge-service-irsa-role"

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
            "${local.oidc_provider_id}:sub" = "system:serviceaccount:llm-judge:judge-service"
            "${local.oidc_provider_id}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = merge(local.iam_tags, {
    Name      = "${var.environment}-judge-service-irsa-role"
    Service   = "judge-service"
    Namespace = "llm-judge"
  })
}

resource "aws_iam_policy" "judge_service_policy" {
  count = local.create_irsa ? 1 : 0

  name        = "${var.environment}-judge-service-policy"
  description = "IAM policy for judge-service in llm-judge namespace"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility"
        ]
        Resource = [var.sqs_queue_arns["judge"]]
      }
    ]
  })

  tags = merge(local.iam_tags, {
    Name      = "${var.environment}-judge-service-policy"
    Service   = "judge-service"
    Namespace = "llm-judge"
  })
}

resource "aws_iam_role_policy_attachment" "judge_service_attachment" {
  count = local.create_irsa ? 1 : 0

  role       = aws_iam_role.judge_service_irsa[0].name
  policy_arn = aws_iam_policy.judge_service_policy[0].arn
}
