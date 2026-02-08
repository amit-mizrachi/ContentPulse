# ========================================================================
# IRSA - INFERENCE SERVICE
# Permissions: SQS consume (inference queue), SNS publish (judge topic)
# Note: No Secrets Manager access - users provide their own LLM API keys
# ========================================================================

resource "aws_iam_role" "inference_service_irsa" {
  count = local.create_irsa ? 1 : 0

  name = "${var.environment}-inference-service-irsa-role"

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
            "${local.oidc_provider_id}:sub" = "system:serviceaccount:llm-judge:inference-service"
            "${local.oidc_provider_id}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = merge(local.iam_tags, {
    Name      = "${var.environment}-inference-service-irsa-role"
    Service   = "inference-service"
    Namespace = "llm-judge"
  })
}

resource "aws_iam_policy" "inference_service_policy" {
  count = local.create_irsa ? 1 : 0

  name        = "${var.environment}-inference-service-policy"
  description = "IAM policy for inference-service in llm-judge namespace"

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
        Resource = [var.sqs_queue_arns["inference"]]
      },
      {
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = [var.sns_topic_arns["judge"]]
      }
    ]
  })

  tags = merge(local.iam_tags, {
    Name      = "${var.environment}-inference-service-policy"
    Service   = "inference-service"
    Namespace = "llm-judge"
  })
}

resource "aws_iam_role_policy_attachment" "inference_service_attachment" {
  count = local.create_irsa ? 1 : 0

  role       = aws_iam_role.inference_service_irsa[0].name
  policy_arn = aws_iam_policy.inference_service_policy[0].arn
}
