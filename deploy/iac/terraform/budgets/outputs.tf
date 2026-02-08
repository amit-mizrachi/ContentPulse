# ========================================================================
# BUDGETS MODULE - OUTPUTS
# ========================================================================

output "budget_ids" {
  description = "Map of budget names to budget IDs"
  value = {
    for key, budget in aws_budgets_budget.monthly_cost :
    key => budget.id
  }
}

output "budget_names" {
  description = "List of budget names"
  value       = [for budget in aws_budgets_budget.monthly_cost : budget.name]
}

output "sns_topic_arn" {
  description = "SNS topic ARN for budget alerts"
  value       = aws_sns_topic.budget_alerts.arn
}

output "budget_details" {
  description = "Detailed information about all budgets"
  value = {
    for key, budget in aws_budgets_budget.monthly_cost :
    key => {
      id           = budget.id
      name         = budget.name
      limit_amount = budget.limit_amount
      limit_unit   = budget.limit_unit
    }
  }
}
