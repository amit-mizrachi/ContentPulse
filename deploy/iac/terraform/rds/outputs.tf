# ========================================================================
# RDS MODULE - OUTPUTS
# ========================================================================

output "db_instance" {
  description = "RDS instance details"
  value = {
    id            = aws_db_instance.llm_judge_mysql.id
    arn           = aws_db_instance.llm_judge_mysql.arn
    endpoint      = aws_db_instance.llm_judge_mysql.endpoint
    address       = aws_db_instance.llm_judge_mysql.address
    port          = aws_db_instance.llm_judge_mysql.port
    database_name = aws_db_instance.llm_judge_mysql.db_name
    resource_id   = aws_db_instance.llm_judge_mysql.resource_id
  }
}

output "db_credentials" {
  description = "Database credentials (sensitive)"
  value = {
    username = aws_db_instance.llm_judge_mysql.username
    password = random_password.rds_master_password.result
    host     = aws_db_instance.llm_judge_mysql.address
    port     = aws_db_instance.llm_judge_mysql.port
    database = aws_db_instance.llm_judge_mysql.db_name
  }
  sensitive = true
}

output "db_subnet_group_name" {
  description = "DB subnet group name"
  value       = aws_db_subnet_group.rds_subnet_group.name
}

output "db_parameter_group_name" {
  description = "DB parameter group name"
  value       = aws_db_parameter_group.mysql_parameter_group.name
}
