# ========================================================================
# SQS QUEUE POLICIES
# IAM policies allowing SNS topics to publish to queues
# ========================================================================

data "aws_iam_policy_document" "sqs_queue_policy_documents" {
  for_each = var.sqs_queue_subscriptions

  # Owner statement - full access for account
  statement {
    sid    = "__owner_statement"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.aws_account_id}:root"]
    }

    actions = ["SQS:*"]
    resources = [
      "arn:aws:sqs:${var.aws_region}:${var.aws_account_id}:${var.environment}-${var.sqs_queue_names[each.key]}-queue"
    ]
  }

  # SNS topic subscription statements
  dynamic "statement" {
    for_each = each.value
    iterator = topic
    content {
      sid    = "topic-subscription-arn:aws:sns:${var.aws_region}:${var.aws_account_id}:${var.environment}-${topic.value}-topic"
      effect = "Allow"

      principals {
        type        = "AWS"
        identifiers = ["*"]
      }

      actions = ["SQS:SendMessage"]

      resources = [
        "arn:aws:sqs:${var.aws_region}:${var.aws_account_id}:${var.environment}-${var.sqs_queue_names[each.key]}-queue"
      ]

      condition {
        test     = "ArnLike"
        variable = "aws:SourceArn"
        values = [
          "arn:aws:sns:${var.aws_region}:${var.aws_account_id}:${var.environment}-${topic.value}-topic"
        ]
      }
    }
  }
}

resource "aws_sqs_queue_policy" "sqs_queue_policies" {
  for_each  = var.sqs_queue_subscriptions
  queue_url = aws_sqs_queue.sqs_queues[each.key].id
  policy    = data.aws_iam_policy_document.sqs_queue_policy_documents[each.key].json
}
