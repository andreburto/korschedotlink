resource "aws_ssm_parameter" "domain_url" {
  name        = "/korsche/domain_url"
  type        = "String"
  value       = var.domain_url
  overwrite   = true
  description = "Domain URL for the korsche application"
}

resource "aws_ssm_parameter" "apigw_url" {
  name        = "/korsche/apigw_url"
  type        = "String"
  value       = aws_api_gateway_deployment.deployment.invoke_url
  overwrite   = true
  description = "API Gateway URL for the korsche application"
}

resource "aws_ssm_parameter" "apigw_arn" {
  name        = "/korsche/apigw_arn"
  type        = "String"
  value       = aws_api_gateway_rest_api.korsche.id
  overwrite   = true
  description = "API Gateway ARN for the korsche application"
}

resource "aws_ssm_parameter" "apigw_stage_name" {
  name        = "/korsche/apigw_stage_name"
  type        = "String"
  value       = aws_api_gateway_deployment.deployment.stage_name
  overwrite   = true
  description = "API Gateway Stage Name for the korsche application"
}
