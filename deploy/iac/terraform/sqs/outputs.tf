# ========================================================================
# SQS MODULE - OUTPUTS
# ========================================================================

output "sqs_queues" {
  description = "Map of SQS queues with standardized output structure"
  value = {
    for key, queue in aws_sqs_queue.sqs_queues : key => {
      arn  = queue.arn
      id   = queue.id
      url  = queue.url
      name = queue.name
    }
  }
}

output "sqs_dead_letter_queues" {
  description = "Map of SQS dead letter queues with standardized output structure"
  value = {
    for key, dlq in aws_sqs_queue.dead_letter_queues : key => {
      arn  = dlq.arn
      id   = dlq.id
      url  = dlq.url
      name = dlq.name
    }
  }
}

output "sns_subscriptions" {
  description = "Map of SNS to SQS subscriptions"
  value = {
    for key, sub in aws_sns_topic_subscription.sns_to_sqs_subscriptions : key => {
      arn      = sub.arn
      topic    = sub.topic_arn
      endpoint = sub.endpoint
    }
  }
}
