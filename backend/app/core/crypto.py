"""マイナンバー等の高機密値をアプリ層で暗号化/復号する。

Fernet(対称鍵)を使用。鍵は JWT_SECRET から導出する（本番は専用鍵を環境変数で）。
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _fernet() -> Fernet:
    # JWT_SECRET から32byte鍵を導出してFernet鍵(base64url)にする
    digest = hashlib.sha256(settings.jwt_secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt(plain: str) -> str:
    return _fernet().encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str | None:
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return None
