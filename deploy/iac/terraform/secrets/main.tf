# ========================================================================
# SIMPLE_SPORT_NEWS SECRETS - GENERIC FOR_EACH PATTERN
# Creates secret containers only. Values set manually.
# ========================================================================

resource "aws_secretsmanager_secret" "secrets" {
  for_each = var.secrets_config

  name        = each.value.name
  description = each.value.description

  tags = merge(var.common_tags, {
    Name = each.value.name
  })
}
