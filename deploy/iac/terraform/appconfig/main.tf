resource "aws_appconfig_application" "simple-sport-news" {
  name        = var.appconfig_config.application_name
  description = var.appconfig_config.application_description
  tags        = var.common_tags
}

resource "aws_appconfig_environment" "this" {
  application_id = aws_appconfig_application.simple-sport-news.id
  name           = var.appconfig_config.environment_name
  description    = var.appconfig_config.environment_description
  tags           = var.common_tags
}

resource "aws_appconfig_configuration_profile" "runtime" {
  application_id = aws_appconfig_application.simple-sport-news.id
  name           = var.appconfig_config.configuration_profile_name
  description    = var.appconfig_config.configuration_profile_description
  location_uri   = "hosted"
  tags           = var.common_tags
}

resource "aws_appconfig_deployment_strategy" "this" {
  name                           = var.appconfig_config.deployment_strategy.name
  deployment_duration_in_minutes = var.appconfig_config.deployment_strategy.deployment_duration_in_minutes
  growth_factor                  = var.appconfig_config.deployment_strategy.growth_factor
  final_bake_time_in_minutes     = var.appconfig_config.deployment_strategy.final_bake_time_in_minutes
  growth_type                    = var.appconfig_config.deployment_strategy.growth_type
  replicate_to                   = "NONE"
  tags                           = var.common_tags
}

resource "aws_appconfig_hosted_configuration_version" "runtime" {
  application_id           = aws_appconfig_application.simple-sport-news.id
  configuration_profile_id = aws_appconfig_configuration_profile.runtime.configuration_profile_id
  content_type             = "application/json"

  # Merge static config from configuration.hcl with dynamic infrastructure values
  content = jsonencode(merge(
    var.appconfig_config.configuration_content,
    {
      # Override SQS with queue URLs from SQS module
      sqs = merge(
        try(var.appconfig_config.configuration_content.sqs, {}),
        {
          content_processing_queue_url = var.sqs_queue_urls["content_processing"]
          query_answering_queue_url    = var.sqs_queue_urls["query_answering"]
        }
      )
      # SNS topic ARNs from SNS module
      sns = {
        content_processing_topic_arn = var.sns_topic_arns["content_processing"]
        query_answering_topic_arn    = var.sns_topic_arns["query_answering"]
      }
      # Redis config from configuration.hcl (K8s Redis)
      redis = {
        host                = var.redis_host
        port                = var.redis_port
        default_ttl_seconds = try(var.appconfig_config.configuration_content.redis.default_ttl_seconds, 3600)
      }
    }
  ))
}

resource "aws_appconfig_deployment" "runtime" {
  application_id           = aws_appconfig_application.simple-sport-news.id
  environment_id           = aws_appconfig_environment.this.environment_id
  configuration_profile_id = aws_appconfig_configuration_profile.runtime.configuration_profile_id
  configuration_version    = aws_appconfig_hosted_configuration_version.runtime.version_number
  deployment_strategy_id   = aws_appconfig_deployment_strategy.this.id
  tags                     = var.common_tags
}
