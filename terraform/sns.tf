resource "aws_sns_topic" "processing_notifications" {
  name = "${var.project_name}-notifications"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.processing_notifications.arn
  protocol  = "email"
  endpoint  = var.notification_email

}