# CDK デプロイ（frontend/dist と ECR イメージが揃ってから実行）
$ErrorActionPreference = "Stop"
$ROOT = Split-Path $PSScriptRoot -Parent
Set-Location "$ROOT\cdk"
if (-not (Test-Path node_modules)) { npm install }
$env:AWS_REGION = "ap-northeast-1"
npx cdk deploy --require-approval never
