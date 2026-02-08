locals {
  secret_tags = {
  }
}

resource "aws_secretsmanager_secret" "rds_credentials" {
  name        = var.secrets_config.rds_credentials.name
  description = var.secrets_config.rds_credentials.description

  tags = merge(local.secret_tags, {
    Name = var.secrets_config.rds_credentials.name
  })
}

resource "aws_secretsmanager_secret_version" "rds_credentials" {
  secret_id = aws_secretsmanager_secret.rds_credentials.id
  secret_string = jsonencode({
    username = var.rds_credentials.username
    password = var.rds_credentials.password
    host     = var.rds_credentials.host
    port     = var.rds_credentials.port
    database = var.rds_credentials.database
  })
}
