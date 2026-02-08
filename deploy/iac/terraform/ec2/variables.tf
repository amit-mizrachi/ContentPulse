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
variable "ec2_config" {
  type = object({
    nat = object({
      instance_type         = string
      volume_size           = number
      volume_type           = string
      delete_on_termination = bool
    })
  })
  description = "EC2 instance configurations"
}

variable "vpc_public_subnets" {
  type = list(object({
    id                = string
    availability_zone = string
  }))
  description = "List of VPC public subnets"
}

variable "vpc_private_route_table_ids" {
  type        = map(string)
  description = "Map of private route table IDs that need NAT routing"
}

variable "iam_nat_router_instance_profile" {
  type = object({
    name = string
    arn  = string
  })
  description = "IAM instance profile for NAT router"
}

variable "sg_nat_security_group_ids" {
  type        = list(string)
  description = "List of security group IDs for NAT instances"
}
