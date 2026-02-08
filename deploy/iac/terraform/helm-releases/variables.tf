# ========================================================================
# HELM RELEASES MODULE - VARIABLES
# ========================================================================

# ========================================================================
# CORE VARIABLES
# ========================================================================
variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "repo_root" {
  description = "Absolute path to the repository root"
  type        = string
}

# ========================================================================
# EKS CLUSTER CONFIGURATION
# ========================================================================
variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
}

variable "cluster_endpoint" {
  description = "EKS cluster endpoint URL"
  type        = string
}

variable "cluster_ca_certificate" {
  description = "EKS cluster certificate authority data (base64 encoded)"
  type        = string
}

variable "cluster_oidc_provider_arn" {
  description = "EKS OIDC provider ARN"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for AWS Load Balancer Controller"
  type        = string
}

# ========================================================================
# KUBERNETES CONFIGURATION
# ========================================================================
variable "namespace" {
  description = "Kubernetes namespace for application services"
  type        = string
  default     = "llm-judge"
}

# ========================================================================
# IAM ROLES (IRSA)
# ========================================================================
variable "iam_role_arns" {
  description = "Map of service name to IRSA role ARN"
  type        = map(string)
}

# ========================================================================
# SECRETS CONFIGURATION
# ========================================================================
variable "secrets_config" {
  description = "Secrets Manager configuration"
  type = object({
    rds_credentials = object({
      name = string
      arn  = string
    })
  })
}

# ========================================================================
# APPCONFIG CONFIGURATION
# ========================================================================
variable "appconfig_ids" {
  description = "AppConfig resource IDs"
  type = object({
    application_id = string
    environment_id = string
    profile_id     = string
  })
}

# ========================================================================
# ECR CONFIGURATION
# ========================================================================
variable "ecr_repository_prefix" {
  description = "ECR repository prefix (account.dkr.ecr.region.amazonaws.com)"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "v1.0.0"
}

# ========================================================================
# SERVICE CONFIGURATION
# ========================================================================
variable "service_names" {
  description = "Map of service names"
  type = object({
    gateway     = string
    redis       = string
    persistence = string
    inference   = string
    judge       = string
  })
}

variable "service_ports" {
  description = "Map of service ports"
  type = object({
    gateway     = number
    redis       = number
    persistence = number
    inference   = number
    judge       = number
  })
}

# ========================================================================
# INFRASTRUCTURE ENDPOINTS
# ========================================================================
variable "infrastructure_endpoints" {
  description = "Infrastructure service endpoints"
  type = object({
    redis_cache = object({
      host = string
      port = number
    })
    rds = object({
      host = string
      port = number
    })
  })
}

# ========================================================================
# SQS CONFIGURATION
# ========================================================================
variable "sqs_queue_urls" {
  description = "SQS queue URLs"
  type        = map(string)
}

# ========================================================================
# SNS CONFIGURATION
# ========================================================================
variable "sns_topic_arns" {
  description = "SNS topic ARNs"
  type        = map(string)
}

# ========================================================================
# AUTOSCALING CONFIGURATION
# ========================================================================
variable "autoscaling" {
  description = "Autoscaling configuration for services"
  type = object({
    cpu_target_percent = number
    services = map(object({
      min_replicas = number
      max_replicas = number
    }))
  })
}

# ========================================================================
# COMMON TAGS
# ========================================================================
variable "common_tags" {
  description = "Common tags to apply to resources"
  type        = map(string)
  default     = {}
}
