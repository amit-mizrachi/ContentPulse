variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g., dev, staging, prod)"
  type        = string
}

variable "project_name" {
  description = "Name of the project for resource naming and tagging"
  type        = string
}

variable "appconfig_config" {
  description = "AppConfig application and profile configuration"
  type = object({
    application_name                  = string
    application_description           = string
    environment_name                  = string
    environment_description           = string
    configuration_profile_name        = string
    configuration_profile_description = string
    configuration_content             = any  # Flexible: accepts full runtime config from configuration.hcl
    deployment_strategy = object({
      name                           = string
      deployment_duration_in_minutes = number
      growth_factor                  = number
      final_bake_time_in_minutes     = number
      growth_type                    = optional(string, "LINEAR")
    })
  })
}

variable "sqs_queue_urls" {
  description = "Map of SQS queue names to their URLs"
  type        = map(string)
}

variable "sns_topic_arns" {
  description = "Map of SNS topic names to their ARNs"
  type        = map(string)
}

variable "redis_host" {
  description = "Redis hostname (Kubernetes service DNS or external endpoint)"
  type        = string
}

variable "redis_port" {
  description = "Redis port number"
  type        = number
  default     = 6379
}

variable "rds_endpoint" {
  description = "RDS instance endpoint address"
  type        = string
}

variable "rds_port" {
  description = "RDS instance port number"
  type        = number
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
