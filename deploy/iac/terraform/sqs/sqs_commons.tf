# ========================================================================
# SQS COMMONS - SHARED LOCALS
# ========================================================================

locals {
  # Flatten queue-to-topic subscriptions: {queue_name: [topic_names...]} -> {"queue.topic": {queue, topic}}
  flattened_sqs_subscriptions = merge([
    for queue_name, topic_names in var.sqs_queue_subscriptions : {
      for topic_name in topic_names :
      "${queue_name}.${topic_name}" => {
        queue_name = queue_name
        topic_name = topic_name
      }
    }
  ]...)

  # DLQ configuration constants
  dlq_max_retention_seconds      = 1209600 # 14 days (AWS maximum)
  dlq_default_visibility_timeout = 300     # 5 minutes
}
