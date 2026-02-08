# ========================================================================
# BUDGETS MODULE - AWS COST BUDGETS
# Creates monthly cost budgets with email notifications
# ========================================================================

locals {
  # Create a map of budgets from the threshold list
  budgets = {
    for threshold in var.budget_thresholds :
    "budget-${threshold}" => {
      amount    = threshold
      threshold = threshold
    }
  }

  # Budget name prefix
  budget_prefix = join("-", [var.environment, var.project_name])
}

# SNS Topic for Budget Alerts
resource "aws_sns_topic" "budget_alerts" {
  name         = "${local.budget_prefix}-budget-alerts"
  display_name = "Budget Alerts for ${var.project_name} ${var.environment}"

  tags = merge(
    var.common_tags,
    {
      Name = "${local.budget_prefix}-budget-alerts"
    }
  )
}

# SNS Topic Subscription (Email)
resource "aws_sns_topic_subscription" "budget_email" {
  topic_arn = aws_sns_topic.budget_alerts.arn
  protocol  = "email"
  endpoint  = var.budget_alert_email
}

# Budget Resources - One per threshold
resource "aws_budgets_budget" "monthly_cost" {
  for_each = local.budgets

  name              = "${local.budget_prefix}-${each.key}"
  budget_type       = "COST"
  limit_amount      = each.value.amount
  limit_unit        = "USD"
  time_unit         = "MONTHLY"
  time_period_start = "2025-01-01_00:00"

  # 80% Actual Spend Alert
  notification {
    comparison_operator       = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_sns_topic_arns = [aws_sns_topic.budget_alerts.arn]
  }

  # 100% Actual Spend Alert
  notification {
    comparison_operator       = "GREATER_THAN"
    threshold                 = 100
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_sns_topic_arns = [aws_sns_topic.budget_alerts.arn]
  }

  # 100% Forecasted Spend Alert
  notification {
    comparison_operator       = "GREATER_THAN"
    threshold                 = 100
    threshold_type            = "PERCENTAGE"
    notification_type         = "FORECASTED"
    subscriber_sns_topic_arns = [aws_sns_topic.budget_alerts.arn]
  }

  tags = merge(
    var.common_tags,
    {
      Name      = "${local.budget_prefix}-${each.key}"
      Threshold = "${each.value.amount}"
    }
  )
}
