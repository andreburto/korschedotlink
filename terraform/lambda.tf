data "archive_file" "korsche" {
  type = "zip"
  source_file = "index.py"
  output_path = "index.zip"
}

resource "aws_lambda_function" "korsche" {
  function_name = "korsche"
  handler = "index.lambda_handler"
  runtime = "python3.10"
  role = aws_iam_role.lambda.arn
  filename = data.archive_file.korsche.output_path
  source_code_hash = data.archive_file.korsche.output_base64sha256
  timeout = 60
  memory_size = 128

  environment {
    variables = {
      BUCKET_NAME = var.domain_url
      PREFIX = "kirsche"
    }
  }
}
