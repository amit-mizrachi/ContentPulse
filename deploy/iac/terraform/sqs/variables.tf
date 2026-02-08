# Core variables (mandatory for all Norman modules)
variable "aws_account_id" {
  type        = string
  description = "AWS Account ID"
}

variable "aws_region" {
  type        = string
  description = "AWS Region"
}

variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"
}

# Module-specific variables
variable "sqs_queue_names" {
  type        = map(string)
  description = "Map of logical queue names to actual queue name suffixes"
}

variable "sqs_queue_subscriptions" {
  type        = map(list(string))
  description = "Map of queue names to list of SNS topic names they subscribe to"
}

variable "sqs_queue_properties" {
  type = object({
    delay_seconds             = number
    max_message_size          = number
    message_retention_seconds = number
    receive_wait_time_seconds = number
  })
  description = "Common properties for all SQS queues"
}

variable "sqs_queue_visibility_timeout_seconds" {
  type        = map(number)
  description = "Visibility timeout in seconds for each queue"
}

variable "sqs_queue_max_receive_count" {
  type        = map(number)
  description = "Maximum receive count before message goes to DLQ"
}
