variable "aws_region" {
  description = "AWS region for the production lakehouse bucket."
  type        = string
  default     = "us-east-1"
}

variable "lakehouse_bucket_name" {
  description = "Globally unique bucket name for raw, silver, and gold lakehouse prefixes."
  type        = string
  default     = "replace-me-lakehouse-platform"
}
