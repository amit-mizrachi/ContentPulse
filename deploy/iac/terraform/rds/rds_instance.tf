# ========================================================================
# LLM JUDGE MYSQL INSTANCE
# Primary RDS MySQL database for the LLM Judge platform
# ========================================================================

resource "aws_db_instance" "llm_judge_mysql" {
  identifier = var.rds_config.identifier

  # Engine
  engine         = var.rds_config.engine
  engine_version = var.rds_config.engine_version
  instance_class = var.rds_config.instance_class

  # Storage
  allocated_storage     = var.rds_config.allocated_storage
  max_allocated_storage = var.rds_config.max_allocated_storage
  storage_type          = var.rds_config.storage_type
  storage_encrypted     = var.rds_config.storage_encrypted

  # Database
  db_name  = var.rds_config.database_name
  username = var.rds_config.username
  password = random_password.rds_master_password.result
  port     = var.rds_config.database_port

  # Network
  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [var.security_group_id]
  multi_az               = var.rds_config.multi_az
  publicly_accessible    = false

  # Backup
  backup_retention_period   = var.rds_config.backup_retention_period
  backup_window             = var.rds_config.backup_window
  maintenance_window        = var.rds_config.maintenance_window
  skip_final_snapshot       = var.rds_config.skip_final_snapshot
  final_snapshot_identifier = var.rds_config.skip_final_snapshot ? null : var.rds_config.final_snapshot_identifier

  # Monitoring
  performance_insights_enabled          = var.rds_config.performance_insights_enabled
  performance_insights_retention_period = var.rds_config.performance_insights_retention
  enabled_cloudwatch_logs_exports       = ["error", "general", "slowquery"]

  # IAM Database Authentication
  iam_database_authentication_enabled = var.rds_config.iam_database_authentication_enabled

  # Parameter group
  parameter_group_name = aws_db_parameter_group.mysql_parameter_group.name

  # Deletion protection (enabled for prod)
  deletion_protection = var.environment == "prod" ? true : false

  # Auto minor version upgrade
  auto_minor_version_upgrade = true

  tags = merge(local.rds_tags, {
    Name = var.rds_config.identifier
  })
}
