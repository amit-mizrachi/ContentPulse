# ========================================================================
# VARIABLES - K8S CONFIG MODULE
# ========================================================================
# All values come from Terragrunt configuration.hcl (Single Source of Truth)
# ========================================================================

variable "namespace" {
  description = "Kubernetes namespace for the ConfigMap"
  type        = string
}

variable "project_name" {
  description = "Project name for labeling"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

variable "service_ports" {
  description = "Service ports configuration"
  type = object({
    gateway     = number
    redis       = number
    persistence = number
    inference   = number
    judge       = number
  })
}

variable "infrastructure_ports" {
  description = "Infrastructure ports configuration"
  type = object({
    redis_cache = number
    mysql       = number
    dns         = number
    https       = number
  })
}

variable "service_names" {
  description = "Service names for discovery"
  type = object({
    gateway     = string
    redis       = string
    persistence = string
    inference   = string
    judge       = string
  })
}

variable "health_check" {
  description = "Health check configuration"
  type = object({
    interval_seconds = number
    timeout_seconds  = number
    retries          = number
    path             = string
  })
}

variable "http_timeouts" {
  description = "HTTP client timeout configuration"
  type = object({
    redis_client           = number
    persistence_client     = number
    judge_inference_client = number
  })
}

variable "autoscaling_cpu_target" {
  description = "CPU target percentage for autoscaling"
  type        = number
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "ecr_repository_prefix" {
  description = "ECR repository prefix"
  type        = string
}

variable "ecr_image_tag" {
  description = "Default ECR image tag"
  type        = string
}

variable "sqs_worker_config" {
  description = "SQS worker configuration"
  type = object({
    max_worker_count                      = number
    visibility_timeout_seconds            = number
    visibility_extension_interval_seconds = number
    max_message_process_time_seconds      = number
    consumer_shutdown_timeout_seconds     = number
    seconds_between_receive_attempts      = number
    wait_time_seconds                     = number
  })
}

variable "common_tags" {
  description = "Common tags for resources"
  type        = map(string)
  default     = {}
}
