# ECR リポジトリ作成（初回のみ）
$env:AWS_REGION = "ap-northeast-1"
aws ecr create-repository --repository-name sons02-demo01-backend --region ap-northeast-1
Write-Host "done (already-exists エラーは無視してOK)"
