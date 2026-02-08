# Core variables (mandatory for all Norman modules)
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
  description = "Environment name (dev, staging, prod)"
}

# Module-specific variables
variable "sns_topic_names" {
  type        = set(string)
  description = "Set of SNS topic names to create"
}
