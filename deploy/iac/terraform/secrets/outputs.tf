output "secrets" {
  description = "Map of secrets with standardized output structure"
  value = {
    rds_credentials = {
      arn  = aws_secretsmanager_secret.rds_credentials.arn
      id   = aws_secretsmanager_secret.rds_credentials.id
      name = aws_secretsmanager_secret.rds_credentials.name
    }
    # Note: OpenAI and Google API keys are NOT stored here.
    # Users provide their own API keys per-request (BYOK model).
    # This eliminates platform LLM costs and simplifies secrets management.
  }
}
