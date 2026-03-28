resource "aws_iam_role" "lambda" {
  name = "korsche-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
    {
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }
  ]
})
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "lambda-log-policy"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Effect = "Allow",
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "AWSLambdaBasicExecutionRole" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "AmazonS3ReadOnlyAccess" {
  role      = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

resource "aws_lambda_permission" "apigw_lambda" {
  statement_id = "AllowExecutionFromAPIGateway"
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.korsche.function_name
  principal = "apigateway.amazonaws.com"

  source_arn = "${aws_api_gateway_rest_api.korsche.execution_arn}/*"
}


# Upload files to S3 bucket
# Create IAM user for S3 uploads
resource "aws_iam_user" "korsche_upload" {
  name = "korsche-upload"
}

# Attach S3 full access policy to the upload user
resource "aws_iam_user_policy" "korsche_upload_s3_policy" {
  name = "korsche-upload-s3-policy"
  user = aws_iam_user.korsche_upload.name

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "s3:*"
        ],
        Effect = "Allow",
        Resource = [
          "arn:aws:s3:::${aws_s3_bucket.korsche.id}",
          "arn:aws:s3:::${aws_s3_bucket.korsche.id}/*"
        ]
      }
    ]
  })
}