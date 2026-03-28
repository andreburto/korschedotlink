resource "aws_api_gateway_rest_api" "korsche" {
  name = "CF Test Backend API"
  description = "CF Test Backend API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_resource" "root" {
  rest_api_id = aws_api_gateway_rest_api.korsche.id
  parent_id = aws_api_gateway_rest_api.korsche.root_resource_id
  path_part = "hello"
}

resource "aws_api_gateway_deployment" "deployment" {
  depends_on = [
    # POST
    aws_api_gateway_method.proxy,
    aws_api_gateway_method_response.proxy,
    aws_api_gateway_integration.proxy,
    aws_api_gateway_integration_response.proxy,
  ]

  rest_api_id = aws_api_gateway_rest_api.korsche.id
  stage_name = "kirsche"
}

##### GET Image List #####
resource "aws_api_gateway_method" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.korsche.id
  resource_id = aws_api_gateway_resource.root.id
  http_method = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.korsche.id
  resource_id = aws_api_gateway_resource.root.id
  http_method = aws_api_gateway_method.proxy.http_method
  integration_http_method = "POST"
  type = "AWS"
  uri = aws_lambda_function.korsche.invoke_arn
}

resource "aws_api_gateway_method_response" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.korsche.id
  resource_id = aws_api_gateway_resource.root.id
  http_method = aws_api_gateway_method.proxy.http_method

  status_code = "200"

  //cors section
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_integration_response" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.korsche.id
  resource_id = aws_api_gateway_resource.root.id
  http_method = aws_api_gateway_method.proxy.http_method
  status_code = aws_api_gateway_method_response.proxy.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" =  "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS,HEAD'",
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  depends_on = [
    aws_api_gateway_method.proxy,
    aws_api_gateway_integration.proxy
  ]
}
