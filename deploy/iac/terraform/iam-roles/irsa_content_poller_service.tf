# ========================================================================
# IRSA - CONTENT POLLER SERVICE
# Permissions: Publish to SNS content_processing topic
# ========================================================================

resource "aws_iam_role" "content_poller_service_irsa" {
  count = local.create_irsa ? 1 : 0

  name = "${var.environment}-content-poller-service-irsa-role"

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
            "${local.oidc_provider_id}:sub" = "system:serviceaccount:simple-sport-news:content-poller-service"
            "${local.oidc_provider_id}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = merge(local.iam_tags, {
    Name      = "${var.environment}-content-poller-service-irsa-role"
    Service   = "content-poller-service"
    Namespace = "simple-sport-news"
  })
}

resource "aws_iam_policy" "content_poller_service_policy" {
  count = local.create_irsa ? 1 : 0

  name        = "${var.environment}-content-poller-service-policy"
  description = "IAM policy for content-poller-service in simple-sport-news namespace"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = [var.sns_topic_arns["content_processing"]]
      }
    ]
  })

  tags = merge(local.iam_tags, {
    Name      = "${var.environment}-content-poller-service-policy"
    Service   = "content-poller-service"
    Namespace = "simple-sport-news"
  })
}

resource "aws_iam_role_policy_attachment" "content_poller_service_attachment" {
  count = local.create_irsa ? 1 : 0

  role       = aws_iam_role.content_poller_service_irsa[0].name
  policy_arn = aws_iam_policy.content_poller_service_policy[0].arn
}
