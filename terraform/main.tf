terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    encrypt = true
    bucket = "mothersect-tf-state"
    dynamodb_table = "mothersect-tf-state-lock"
    key    = "korsche"
    region = "us-east-1"
  }
}

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region
}

# Can possibly be replaced with the template module.
# https://registry.terraform.io/modules/hashicorp/dir/template/latest
locals {
  s3_origin_id = var.domain_url
  cf_logs_bucket = join("-", [replace(var.domain_url, ".", "-"), "logs"])
}

resource "aws_s3_bucket" "korsche" {
  bucket = var.domain_url
}

# Enable public access for the S3 bucket
resource "aws_s3_bucket_public_access_block" "korsche" {
  bucket = aws_s3_bucket.korsche.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Apply public read policy to the bucket
resource "aws_s3_bucket_policy" "korsche_public_read" {
  bucket = aws_s3_bucket.korsche.id
  policy = data.aws_iam_policy_document.korsche_public_read.json

  depends_on = [aws_s3_bucket_public_access_block.korsche]
}

data "aws_iam_policy_document" "korsche_public_read" {
  statement {
    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    actions = [
      "s3:GetObject",
    ]

    resources = [
      "${aws_s3_bucket.korsche.arn}/*",
    ]
  }
}

resource "aws_s3_bucket_ownership_controls" "korsche" {
  bucket = aws_s3_bucket.korsche.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_website_configuration" "korsche" {
  bucket = aws_s3_bucket.korsche.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

resource "aws_route53_record" "korsche" {
  zone_id = var.zone_id
  name    = "${var.domain_url}."
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.korsche.domain_name
    zone_id                = aws_cloudfront_distribution.korsche.hosted_zone_id
    evaluate_target_health = false
  }
}

# Load the source files.
resource "aws_s3_object" "index" {
  content_type = "text/html"
  bucket       = aws_s3_bucket.korsche.id
  key          = "index.html"
  source       = "index.html"
  etag        = filemd5("index.html")
}
