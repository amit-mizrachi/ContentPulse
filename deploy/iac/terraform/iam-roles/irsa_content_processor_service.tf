# ========================================================================
# IRSA - CONTENT PROCESSOR SERVICE
# Permissions: Consume from SQS content_processing queue,
#              Read secrets from SecretsManager (LLM credentials)
# ========================================================================

resource "aws_iam_role" "content_processor_service_irsa" {
  count = local.create_irsa ? 1 : 0

  name = "${var.environment}-content-processor-service-irsa-role"

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
            "${local.oidc_provider_id}:sub" = "system:serviceaccount:simple-sport-news:content-processor-service"
            "${local.oidc_provider_id}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = merge(local.iam_tags, {
    Name      = "${var.environment}-content-processor-service-irsa-role"
    Service   = "content-processor-service"
    Namespace = "simple-sport-news"
  })
}

resource "aws_iam_policy" "content_processor_service_policy" {
  count = local.create_irsa ? 1 : 0

  name        = "${var.environment}-content-processor-service-policy"
  description = "IAM policy for content-processor-service in simple-sport-news namespace"

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
        Resource = [var.sqs_queue_arns["content_processing"]]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = ["arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:${var.environment}/${var.project_name}/llm/*"]
      }
    ]
  })

  tags = merge(local.iam_tags, {
    Name      = "${var.environment}-content-processor-service-policy"
    Service   = "content-processor-service"
    Namespace = "simple-sport-news"
  })
}

resource "aws_iam_role_policy_attachment" "content_processor_service_attachment" {
  count = local.create_irsa ? 1 : 0

  role       = aws_iam_role.content_processor_service_irsa[0].name
  policy_arn = aws_iam_policy.content_processor_service_policy[0].arn
}
