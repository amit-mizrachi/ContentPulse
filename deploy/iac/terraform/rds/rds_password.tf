# ========================================================================
# RDS MASTER PASSWORD
# Generates a secure random password for the database master user
# ========================================================================

resource "random_password" "rds_master_password" {
  length  = 32
  special = true
  # Exclude characters that might cause issues in connection strings
  override_special = "!#$%&*()-_=+[]{}<>:?"
}
