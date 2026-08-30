resource "aws_ecr_repository" "image_processor" {
  name                 = "${var.project_name}-image-processor"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Keep the repo tidy — only retain the 10 most recent images
resource "aws_ecr_lifecycle_policy" "image_processor" {
  repository = aws_ecr_repository.image_processor.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep only the last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}