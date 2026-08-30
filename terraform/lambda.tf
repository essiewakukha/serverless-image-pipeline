resource "aws_lambda_function" "image_processor" {
  function_name = "${var.project_name}-image-processor"
  role          = aws_iam_role.lambda_execution.arn

  package_type = "Image"
  image_uri    = "${aws_ecr_repository.image_processor.repository_url}:${var.ecr_image_tag}"

  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout

  environment {
    variables = {
      OUTPUT_BUCKET  = aws_s3_bucket.output.bucket
      SNS_TOPIC_ARN  = aws_sns_topic.processing_notifications.arn
      THUMBNAIL_SIZE = var.thumbnail_size
      WATERMARK_TEXT = var.watermark_text
    }
  }

  # Terraform can't deploy a Lambda container image until that image tag
  # already exists in ECR. On a first-ever `terraform apply`, this resource
  # will fail - that's expected. See the README for the two-phase apply.
  depends_on = [aws_ecr_repository.image_processor]
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.image_processor.function_name}"
  retention_in_days = 14
}