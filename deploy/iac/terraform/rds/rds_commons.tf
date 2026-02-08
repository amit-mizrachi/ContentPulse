# ========================================================================
# RDS COMMONS - SHARED LOCALS
# ========================================================================

locals {
  name_prefix = join("-", [var.environment, var.project_name])
  rds_tags    = var.common_tags
}
