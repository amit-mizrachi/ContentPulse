# ========================================================================
# SQS MODULE - TERRAGRUNT WRAPPER
# Dependency Group 1: Foundational (depends on SNS for subscriptions)
# ========================================================================

include "root" {
  path   = find_in_parent_folders("root.hcl")
  expose = true
}

dependency "sns" {
  config_path = "../sns"

  mock_outputs = {
    sns_topics = {
      inference = {
        arn  = "arn:aws:sns:us-east-1:123456789012:mock-inference-topic"
        id   = "mock-inference-topic"
        name = "dev-nadav-inference-topic"
      }
      judge = {
        arn  = "arn:aws:sns:us-east-1:123456789012:mock-judge-topic"
        id   = "mock-judge-topic"
        name = "dev-nadav-judge-topic"
      }
    }
  }

  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

terraform {
  source = "${include.root.locals.repo_root}/deploy/iac/terraform/sqs"
}

inputs = {
  # Core variables
  aws_account_id     = include.root.inputs.aws_account_id
  aws_region         = include.root.inputs.aws_region
  environment         = include.root.inputs.environment

  # SQS configuration
  sqs_queue_names                      = include.root.inputs.sqs_config.queue_names
  sqs_queue_subscriptions              = include.root.inputs.sqs_config.queue_subscriptions
  sqs_queue_properties                 = include.root.inputs.sqs_config.queue_properties
  sqs_queue_visibility_timeout_seconds = include.root.inputs.sqs_config.queue_visibility_timeout_seconds
  sqs_queue_max_receive_count          = include.root.inputs.sqs_config.queue_max_receive_count
}
