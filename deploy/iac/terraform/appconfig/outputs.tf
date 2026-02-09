output "appconfig_application" {
  description = "AppConfig application details"
  value = {
    id   = aws_appconfig_application.simple-sport-news.id
    arn  = aws_appconfig_application.simple-sport-news.arn
    name = aws_appconfig_application.simple-sport-news.name
  }
}

output "appconfig_environment" {
  description = "AppConfig environment details"
  value = {
    id   = aws_appconfig_environment.this.environment_id
    name = aws_appconfig_environment.this.name
  }
}

output "appconfig_profile" {
  description = "AppConfig configuration profile details"
  value = {
    id   = aws_appconfig_configuration_profile.runtime.configuration_profile_id
    arn  = aws_appconfig_configuration_profile.runtime.arn
    name = aws_appconfig_configuration_profile.runtime.name
  }
}

output "appconfig_deployment_strategy" {
  description = "AppConfig deployment strategy details"
  value = {
    id   = aws_appconfig_deployment_strategy.this.id
    arn  = aws_appconfig_deployment_strategy.this.arn
    name = aws_appconfig_deployment_strategy.this.name
  }
}

output "appconfig_deployment" {
  description = "AppConfig deployment details"
  value = {
    deployment_number     = aws_appconfig_deployment.runtime.deployment_number
    configuration_version = aws_appconfig_hosted_configuration_version.runtime.version_number
  }
}
