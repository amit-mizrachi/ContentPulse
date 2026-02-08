variable "aws_account_id" { type = string }
variable "aws_region" { type = string }
variable "environment" { type = string }
variable "project_name" { type = string }

variable "secrets_config" {
  type = map(object({
    name        = string
    description = string
    secret_data = map(string)
  }))
}

variable "rds_credentials" {
  type = object({
    username = string
    password = string
    host     = string
    port     = number
    database = string
  })
  sensitive = true
}

variable "common_tags" {
  type    = map(string)
  default = {}
}
