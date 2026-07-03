"""Okta アクセストークン(RS256)の検証。

JWKS(公開鍵セット)を Okta から取得・キャッシュし、署名/issuer/audience/期限を検証する。
API Gateway の JWT authorizer でも同じ検証をしているが、
バックエンド自身でも検証する（多層防御・ローカル実行時の担保）。
"""
import json
import time
import urllib.request

from jose import jwt

from app.core.config import settings

_jwks_cache: dict = {"keys": [], "fetched_at": 0.0}
_JWKS_TTL_SEC = 3600.0


def _get_jwks() -> list[dict]:
    now = time.time()
    if not _jwks_cache["keys"] or now - _jwks_cache["fetched_at"] > _JWKS_TTL_SEC:
        url = f"{settings.okta_issuer}/v1/keys"
        with urllib.request.urlopen(url, timeout=5) as res:
            _jwks_cache["keys"] = json.loads(res.read())["keys"]
            _jwks_cache["fetched_at"] = now
    return _jwks_cache["keys"]


def verify_okta_token(token: str) -> dict | None:
    """署名・iss・aud・exp を検証して claims を返す。失敗時は None。"""
    try:
        kid = jwt.get_unverified_header(token).get("kid")
        key = next((k for k in _get_jwks() if k.get("kid") == kid), None)
        if key is None:
            # 鍵ローテーション直後の可能性 → キャッシュを捨てて再取得
            _jwks_cache["fetched_at"] = 0.0
            key = next((k for k in _get_jwks() if k.get("kid") == kid), None)
        if key is None:
            return None
        return jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.okta_audience,
            issuer=settings.okta_issuer,
        )
    except Exception:
        return None
