# ========================================================================
# IAM ROLES MODULE - INPUT VARIABLES (IRSA)
# ========================================================================

# Core Norman Variables
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

# Dependencies (IRSA-specific - optional for standalone EKS roles)
variable "eks_cluster_name" {
  type        = string
  description = "EKS cluster name (required for IRSA roles)"
  default     = ""
}

variable "eks_oidc_provider_arn" {
  type        = string
  description = "EKS OIDC provider ARN (required for IRSA roles)"
  default     = ""
}

variable "eks_oidc_provider_url" {
  type        = string
  description = "EKS OIDC provider URL (required for IRSA roles)"
  default     = ""
}

variable "sns_topic_arns" {
  type        = map(string)
  description = "SNS topic ARNs (inference, judge)"
  default     = {}
}

variable "sqs_queue_arns" {
  type        = map(string)
  description = "SQS queue ARNs (inference, judge)"
  default     = {}
}

variable "secret_arns" {
  type        = map(string)
  description = "Secrets Manager secret ARNs"
  default     = {}
}

variable "iam_roles_config" {
  type = map(object({
    service_name = string
    namespace    = string
    policies = list(object({
      effect    = string
      actions   = list(string)
      resources = list(string)
    }))
  }))
  description = "IAM roles configuration for IRSA"
  default     = {}
}

variable "common_tags" {
  type        = map(string)
  description = "Common tags to apply to all resources"
  default     = {}
}

# ========================================================================
# EC2 IAM ROLES VARIABLES
# ========================================================================
variable "ec2_iam_policies" {
  type        = map(map(string))
  description = "Map of EC2 role names to map of policy names and their ARNs"
  default     = {}
}

variable "ec2_assume_role_policy_document" {
  type        = string
  description = "IAM assume role policy document for EC2 instances (JSON string)"
  default     = ""
}
