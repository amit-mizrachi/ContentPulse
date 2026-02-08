# ========================================================================
# SQS QUEUES
# Main message queues for async processing
# ========================================================================

resource "aws_sqs_queue" "sqs_queues" {
  for_each = var.sqs_queue_subscriptions

  name                       = join("-", [var.environment, var.sqs_queue_names[each.key], "queue"])
  delay_seconds              = var.sqs_queue_properties.delay_seconds
  max_message_size           = var.sqs_queue_properties.max_message_size
  message_retention_seconds  = var.sqs_queue_properties.message_retention_seconds
  receive_wait_time_seconds  = var.sqs_queue_properties.receive_wait_time_seconds
  visibility_timeout_seconds = var.sqs_queue_visibility_timeout_seconds[each.key]

  # Dead Letter Queue configuration
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dead_letter_queues[each.key].arn
    maxReceiveCount     = var.sqs_queue_max_receive_count[each.key]
  })

  tags = {}
}
