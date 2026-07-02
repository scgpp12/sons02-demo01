# バックエンドイメージを sons02 でビルドして ECR へ push する
# 前提: Windows→sons02 の ssh 免密、sons02 に docker（sons02 に aws CLI は不要）
$ErrorActionPreference = "Stop"
$REPO = "603319838936.dkr.ecr.ap-northeast-1.amazonaws.com/sons02-demo01-backend"
$ROOT = Split-Path $PSScriptRoot -Parent

# 1) コードを sons02 へ転送（node_modules 等は除外）
Write-Host "[1/3] transfer backend to sons02..."
ssh sons02 "mkdir -p ~/sons02-demo01"
tar czf - -C $ROOT --exclude=__pycache__ --exclude='*.egg-info' backend | ssh sons02 "tar xzf - -C ~/sons02-demo01"

# 2) ECR ログイン（トークンは Windows 側で発行して sons02 の docker に渡す）
Write-Host "[2/3] ecr login on sons02..."
$pw = aws ecr get-login-password --region ap-northeast-1
$pw | ssh sons02 "docker login --username AWS --password-stdin 603319838936.dkr.ecr.ap-northeast-1.amazonaws.com"

# 3) ビルド & push（sons02 は x86_64 なので linux/amd64 ネイティブ）
Write-Host "[3/3] build and push..."
ssh sons02 "cd ~/sons02-demo01/backend && docker build -t ${REPO}:latest . && docker push ${REPO}:latest"
Write-Host "done."
