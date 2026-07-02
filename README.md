# sons02-demo01 — B案アーキテクチャ 個人検証

SBR 営業AIプロジェクトの **B案アーキテクチャ** を個人 AWS 環境（東京）で再現する練習リポジトリ。
UI は Claude で構築した **SES社内管理システム** を流用。

```
ブラウザ
  └─ CloudFront（唯一の入口・*.cloudfront.net）
       ├─ /*      → S3 プライベートバケット + OAC（React SPA）
       └─ /api/*  → HTTP API Gateway（x-origin-verify ヘッダ付与）
                      └─ VPC Link → Cloud Map → ECS Fargate
                           [FastAPI + PostgreSQL サイドカー]
```

## 本番（SBR）との対応と相違

| 項目 | 本番B案 | この検証環境 |
|---|---|---|
| 認証 | Okta OIDC(PKCE) + API GW JWT authorizer | アプリ内蔵 JWT（SESシステム自前ログイン）|
| DB | RDS PostgreSQL | PG サイドカーコンテナ（**データ揮発**）|
| WAF | CloudFront に装着 | なし（コスト節約）|
| 秘密ヘッダ検証 | API GW/アプリで強制 | ヘッダ付与のみ（検証は省略）|
| LLM | Gemini API | なし |

## デプロイ手順（PowerShell）

```powershell
./scripts/1-create-ecr.ps1          # 初回のみ: ECR リポジトリ作成
./scripts/2-build-push-backend.ps1  # sons02 で docker build → ECR push
./scripts/3-build-frontend.ps1      # Vite ビルド（VITE_API_BASE_URL="" で同一オリジン化）
./scripts/4-deploy.ps1              # cdk deploy（初回 ~10分, CloudFront作成のため）
```

出力される `CloudFrontUrl` にアクセス → ログイン: `admin@example.com / Demo2026!`

## 片付け（Fargate 課金停止）

```powershell
./scripts/9-destroy.ps1
```

## コスト目安（東京）

- 稼働中: Fargate(0.5vCPU/1GB) ≈ $18/月 が主。CloudFront/S3/API GW は数十円
- NAT Gateway なし・ALB なし・RDS なし構成
- **練習が終わったら必ず destroy**

## 注意

- PostgreSQL はタスク内サイドカー = タスク再起動でデータ消失（デモ用）
- 管理者パスワード等は検証用の固定値。本番では Secrets Manager / Okta に置き換える
