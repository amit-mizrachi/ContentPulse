# ========================================================================
# SQS DEAD LETTER QUEUES
# Captures messages that fail processing after max retries
# ========================================================================

resource "aws_sqs_queue" "dead_letter_queues" {
  for_each = var.sqs_queue_subscriptions

  name                       = join("-", [var.environment, var.sqs_queue_names[each.key], "dlq"])
  message_retention_seconds  = local.dlq_max_retention_seconds
  visibility_timeout_seconds = local.dlq_default_visibility_timeout

  tags = {}
}
