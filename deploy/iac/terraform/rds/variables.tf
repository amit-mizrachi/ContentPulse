# ========================================================================
# RDS MODULE - INPUT VARIABLES
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

# RDS Configuration
variable "rds_config" {
  type = object({
    identifier                          = string
    engine                              = string
    engine_version                      = string
    instance_class                      = string
    allocated_storage                   = number
    max_allocated_storage               = number
    storage_type                        = string
    storage_encrypted                   = bool
    multi_az                            = bool
    database_name                       = string
    database_port                       = number
    username                            = string
    backup_retention_period             = number
    backup_window                       = string
    maintenance_window                  = string
    skip_final_snapshot                 = bool
    final_snapshot_identifier           = string
    performance_insights_enabled        = bool
    performance_insights_retention      = number
    iam_database_authentication_enabled = bool
    parameter_group_family              = string
    parameters = list(object({
      name  = string
      value = string
    }))
  })
  description = "RDS configuration object"
}

# Dependencies
variable "vpc_id" {
  type        = string
  description = "VPC ID"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnet IDs for RDS subnet group (private data subnets)"
}

variable "security_group_id" {
  type        = string
  description = "Security group ID for RDS"
}

variable "common_tags" {
  type        = map(string)
  description = "Common tags to apply to all resources"
  default     = {}
}
