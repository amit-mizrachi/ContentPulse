output "sns_topics" {
  description = "Map of SNS topics with standardized output structure"
  value = {
    for key, topic in aws_sns_topic.sns_topics : key => {
      arn  = topic.arn
      id   = topic.id
      name = topic.name
    }
  }
}
