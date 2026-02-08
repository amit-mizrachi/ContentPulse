# ========================================================================
# SNS TO SQS SUBSCRIPTIONS
# Wires SNS topics to SQS queues for pub/sub messaging
# ========================================================================

resource "aws_sns_topic_subscription" "sns_to_sqs_subscriptions" {
  for_each  = local.flattened_sqs_subscriptions
  topic_arn = "arn:aws:sns:${var.aws_region}:${var.aws_account_id}:${var.environment}-${each.value["topic_name"]}-topic"
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.sqs_queues[each.value["queue_name"]].arn
}
