# ========================================================================
# ECR MODULE - INPUT VARIABLES
# ========================================================================

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
  description = "Environment name"
}

variable "project_name" {
  type        = string
  description = "Project name"
}

variable "repository_names" {
  type        = list(string)
  description = "List of ECR repository names to create"
  default = [
    "gateway-service",
    "inference-service",
    "judge-service",
    "redis-service",
    "persistence-service",
    "ai-model-service"
  ]
}

variable "common_tags" {
  type        = map(string)
  description = "Common tags to apply to all resources"
  default     = {}
}
