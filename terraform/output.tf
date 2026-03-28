output "url" {
  value = aws_api_gateway_deployment.deployment.invoke_url
}

output "apigw" {
  value = aws_api_gateway_rest_api.korsche.execution_arn
}
