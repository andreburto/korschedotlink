#!/bin/bash
set -euox pipefail

terraform apply -auto-approve

APIGW_ARN=$(aws ssm get-parameter --name "/korsche/apigw_arn" --query "Parameter.Value" --output text)

STAGE_NAME=$(aws ssm get-parameter --name "/korsche/apigw_stage_name" --query "Parameter.Value" --output text)

aws apigateway create-deployment --rest-api-id $APIGW_ARN --stage-name $STAGE_NAME
