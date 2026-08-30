variable "aws_region" {
  description = "AWS region to deploy all resources into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix used for naming all resources (must be globally unique for S3/ECR)"
  type        = string
  default     = "serverless-image-pipeline"
}

variable "notification_email" {
  description = "Email address to receive SNS success/failure notifications"
  type        = string
  # No default on purpose — force the user to set this explicitly in terraform.tfvars
}

variable "ecr_image_tag" {
  description = "Tag of the Docker image in ECR that the Lambda should run. Update this after pushing a new image."
  type        = string
  default     = "latest"
}

variable "thumbnail_size" {
  description = "Max thumbnail dimensions passed to the Lambda as WIDTHxHEIGHT"
  type        = string
  default     = "300x300"
}

variable "watermark_text" {
  description = "Text stamped onto processed images"
  type        = string
  default     = "PROCESSED"
}

variable "lambda_memory_size" {
  description = "Memory (MB) allocated to the Lambda function. Pillow benefits from more memory."
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}