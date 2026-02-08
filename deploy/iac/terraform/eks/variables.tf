# ========================================================================
# EKS MODULE - INPUT VARIABLES
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
  description = "Environment name (e.g., dev, staging, prod)"
}

variable "project_name" {
  type        = string
  description = "Project name"
}

# EKS Configuration
variable "eks_config" {
  type = object({
    cluster_name            = string
    cluster_version         = string
    endpoint_private_access = bool
    endpoint_public_access  = bool

    system_node_group = object({
      name           = string
      instance_types = list(string)
      capacity_type  = string
      desired_size   = number
      min_size       = number
      max_size       = number
      disk_size      = number
      labels         = map(string)
      taints         = list(any)
    })

    app_node_group = object({
      name           = string
      instance_types = list(string)
      capacity_type  = string
      desired_size   = number
      min_size       = number
      max_size       = number
      disk_size      = number
      labels         = map(string)
      taints         = list(any)
    })

    ai_node_group = object({
      enabled        = bool
      name           = string
      instance_types = list(string)
      capacity_type  = string
      desired_size   = number
      min_size       = number
      max_size       = number
      disk_size      = number
      labels         = map(string)
      taints         = list(object({
        key    = string
        value  = string
        effect = string
      }))
    })

    addons = object({
      vpc_cni = object({
        version              = string
        configuration_values = string
      })
      coredns = object({
        version = string
      })
      kube_proxy = object({
        version = string
      })
      ebs_csi_driver = object({
        version = string
      })
    })

    cluster_logging             = list(string)
    enable_container_insights   = bool
  })
  description = "EKS cluster configuration"
}

# Dependencies
variable "vpc_id" {
  type        = string
  description = "VPC ID"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnet IDs for EKS (private app subnets)"
}

variable "eks_nodes_security_group_id" {
  type        = string
  description = "Security group ID for EKS nodes"
}

variable "common_tags" {
  type        = map(string)
  description = "Common tags to apply to all resources"
  default     = {}
}
