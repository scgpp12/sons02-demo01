import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(title="SES社内管理システム API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CloudFront 経由の検証（旁門封じ） ---
# CloudFront がオリジンへ付与する x-origin-verify を検証し、
# API Gateway 直叩き（CloudFront を経由しないアクセス）を 403 で遮断する。
# 環境変数 ORIGIN_VERIFY_SECRET が未設定なら無効（ローカル開発用）。
_ORIGIN_VERIFY_SECRET = os.getenv("ORIGIN_VERIFY_SECRET")

if _ORIGIN_VERIFY_SECRET:

    @app.middleware("http")
    async def verify_origin(request: Request, call_next):
        if request.url.path.startswith("/api"):
            if request.headers.get("x-origin-verify") != _ORIGIN_VERIFY_SECRET:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Forbidden: direct access is not allowed"},
                )
        return await call_next(request)


app.include_router(api_router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


# 機械間通信（IAM SigV4 認証）デモ用。API Gateway 側で AWS_IAM 認証を要求するルート。
@app.get("/internal/ping", tags=["internal"])
def internal_ping() -> dict[str, str]:
    return {"status": "pong", "auth": "iam-sigv4"}
