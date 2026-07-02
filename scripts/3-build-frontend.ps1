# フロントエンドをビルド（CloudFront 同一オリジン構成: API ベースURLは空 = 相対 /api）
$ErrorActionPreference = "Stop"
$ROOT = Split-Path $PSScriptRoot -Parent
Set-Location "$ROOT\frontend"
if (-not (Test-Path node_modules)) { npm ci }
$env:VITE_API_BASE_URL = ""
npm run build
Write-Host "done. -> frontend/dist"
