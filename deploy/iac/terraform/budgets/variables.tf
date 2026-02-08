# ========================================================================
# BUDGETS MODULE - INPUT VARIABLES
# ========================================================================

# Core Variables
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

variable "project_name" {
  type        = string
  description = "Project name"
}

# Budget Configuration
variable "budget_alert_email" {
  type        = string
  description = "Email address to receive budget alerts"
}

variable "budget_thresholds" {
  type        = list(number)
  description = "Budget threshold amounts in USD"
  default     = [50, 100, 150, 200]
}

# Common Tags
variable "common_tags" {
  type        = map(string)
  description = "Common tags to apply to all resources"
  default     = {}
}
