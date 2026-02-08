# ========================================================================
# MYSQL PARAMETER GROUP
# Custom database parameters for MySQL optimization
# ========================================================================

resource "aws_db_parameter_group" "mysql_parameter_group" {
  name   = "${local.name_prefix}-db-params"
  family = var.rds_config.parameter_group_family

  dynamic "parameter" {
    for_each = var.rds_config.parameters
    content {
      name  = parameter.value.name
      value = parameter.value.value
    }
  }

  tags = merge(local.rds_tags, {
    Name = "${local.name_prefix}-db-params"
  })
}
