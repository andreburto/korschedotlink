resource "aws_cloudfront_distribution" "korsche" {
  origin {
    domain_name              = aws_s3_bucket.korsche.bucket_domain_name
    origin_id                = aws_s3_bucket.korsche.id
  }

  enabled             = true
  is_ipv6_enabled     = false
  comment             = "Some comment"
  default_root_object = "index.html"

  aliases = [var.domain_url]

  logging_config {
    include_cookies = false
    bucket          = aws_s3_bucket.korsche_logs.bucket_regional_domain_name
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = aws_s3_bucket.korsche.id
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false

      cookies {
        forward = "all"
      }
    }
  }

  price_class = "PriceClass_100"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = false
    acm_certificate_arn            = aws_acm_certificate.korsche.arn
    ssl_support_method             = "sni-only"
    minimum_protocol_version       = "TLSv1.2_2021"
  }
}