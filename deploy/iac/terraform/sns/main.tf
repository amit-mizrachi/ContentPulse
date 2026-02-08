resource "aws_sns_topic" "sns_topics" {
  for_each = var.sns_topic_names
  name     = join("-", [var.environment, each.value, "topic"])

  tags = {
  }
}
