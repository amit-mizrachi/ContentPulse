include "root" {
  path   = find_in_parent_folders("root.hcl")
  expose = true
}

dependency "sns" {
  config_path = "../sns"
  mock_outputs = {
    sns_topics = {
      content_processing = {
        arn  = "arn:aws:sns:us-east-1:123456789012:mock-content-processing-topic"
        id   = "mock-content-processing-topic"
        name = "dev-simple-sport-news-content-processing-topic"
      }
      query_answering = {
        arn  = "arn:aws:sns:us-east-1:123456789012:mock-query-answering-topic"
        id   = "mock-query-answering-topic"
        name = "dev-simple-sport-news-query-answering-topic"
      }
    }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

terraform {
  source = "${include.root.locals.repo_root}/deploy/iac/terraform/sqs"
}

inputs = {
  aws_account_id                       = include.root.inputs.aws_account_id
  aws_region                           = include.root.inputs.aws_region
  environment                          = include.root.inputs.environment
  sqs_queue_names                      = include.root.inputs.sqs_config.queue_names
  sqs_queue_subscriptions              = include.root.inputs.sqs_config.queue_subscriptions
  sqs_queue_properties                 = include.root.inputs.sqs_config.queue_properties
  sqs_queue_visibility_timeout_seconds = include.root.inputs.sqs_config.queue_visibility_timeout_seconds
  sqs_queue_max_receive_count          = include.root.inputs.sqs_config.queue_max_receive_count
}
