# ========================================================================
# APPCONFIG MODULE - TERRAGRUNT WRAPPER
# Dependency Group 4: Configuration (depends on: sns, sqs, rds)
# ========================================================================

include "root" {
  path   = find_in_parent_folders("root.hcl")
  expose = true
}

dependency "sns" {
  config_path = "../sns"

  mock_outputs = {
    sns_topics = {
      inference = { arn = "arn:aws:sns:${include.root.locals.aws_region}:000000000000:mock-inference-topic" }
      judge     = { arn = "arn:aws:sns:${include.root.locals.aws_region}:000000000000:mock-judge-topic" }
    }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "sqs" {
  config_path = "../sqs"

  mock_outputs = {
    sqs_queues = {
      inference = { url = "https://sqs.${include.root.locals.aws_region}.amazonaws.com/000000000000/mock-inference-queue" }
      judge     = { url = "https://sqs.${include.root.locals.aws_region}.amazonaws.com/000000000000/mock-judge-queue" }
    }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "rds" {
  config_path = "../rds"

  mock_outputs = {
    db_instance = {
      address = "mock-rds.${include.root.locals.aws_region}.rds.amazonaws.com"
      port    = 3306
    }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

terraform {
  source = "${include.root.locals.repo_root}/deploy/iac/terraform/appconfig"
}

inputs = {
  # Core variables
  aws_region   = include.root.inputs.aws_region
  environment  = include.root.inputs.environment
  project_name = include.root.inputs.project_name

  # AppConfig configuration from single source of truth
  appconfig_config = include.root.inputs.appconfig_config

  # Dependencies - runtime values from other modules
  sqs_queue_urls = {
    inference = dependency.sqs.outputs.sqs_queues["inference"].url
    judge     = dependency.sqs.outputs.sqs_queues["judge"].url
  }
  sns_topic_arns = {
    inference = dependency.sns.outputs.sns_topics["inference"].arn
    judge     = dependency.sns.outputs.sns_topics["judge"].arn
  }

  # Redis configuration from single source of truth (Kubernetes Redis)
  redis_host = include.root.inputs.redis_k8s_config.service_dns
  redis_port = include.root.inputs.redis_k8s_config.port

  # RDS configuration from dependency
  rds_endpoint = dependency.rds.outputs.db_instance.address
  rds_port     = dependency.rds.outputs.db_instance.port

  # Common tags
  common_tags = include.root.inputs.common_tags
}
