# 検証終了時に全リソース削除（Fargate 稼働課金を止める）
$ErrorActionPreference = "Stop"
$ROOT = Split-Path $PSScriptRoot -Parent
Set-Location "$ROOT\cdk"
$env:AWS_REGION = "ap-northeast-1"
npx cdk destroy --force
Write-Host "ECR リポジトリ本体は残ります。不要なら: aws ecr delete-repository --repository-name sons02-demo01-backend --force"
