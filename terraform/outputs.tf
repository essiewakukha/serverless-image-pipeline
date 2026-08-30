output "ecr_repository_url" {
  description = "Push your Docker image here (needed before the Lambda can deploy)"
  value       = aws_ecr_repository.image_processor.repository_url
}

output "input_bucket_name" {
  description = "Upload raw images here to trigger processing"
  value       = aws_s3_bucket.input.bucket
}

output "output_bucket_name" {
  description = "Processed thumbnails land here"
  value       = aws_s3_bucket.output.bucket
}

output "lambda_function_name" {
  description = "Name of the deployed Lambda function"
  value       = aws_lambda_function.image_processor.function_name
}

output "sns_topic_arn" {
  description = "SNS topic ARN - remember to confirm the email subscription"
  value       = aws_sns_topic.processing_notifications.arn
}

output "aws_account_id" {
  description = "Your AWS account ID, useful for docker login/push commands"
  value       = data.aws_caller_identity.current.account_id
}