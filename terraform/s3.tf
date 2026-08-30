# ── Input bucket: where users upload raw images ──────────────────────────
resource "aws_s3_bucket" "input" {
  bucket = "${var.project_name}-input"
}

resource "aws_s3_bucket_public_access_block" "input" {
  bucket                  = aws_s3_bucket.input.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "input" {
  bucket = aws_s3_bucket.input.id
  versioning_configuration {
    status = "Disabled"
  }
}

#  Output bucket: where processed thumbnails land 
resource "aws_s3_bucket" "output" {
  bucket = "${var.project_name}-output"
}

resource "aws_s3_bucket_public_access_block" "output" {
  bucket                  = aws_s3_bucket.output.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

#  Event notification: input bucket -> Lambda
resource "aws_s3_bucket_notification" "input_trigger" {
  bucket = aws_s3_bucket.input.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.image_processor.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3_invoke]
}