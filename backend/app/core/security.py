"""パスワードハッシュ(bcrypt)とJWT(python-jose)の生成・検証。

bcryptライブラリを直接使う（passlibはbcrypt4.x系と非互換のため不採用）。
bcryptは先頭72バイトのみ使用するため、長いパスワードは72バイトに切り詰める。
"""
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def _to_bytes(plain: str) -> bytes:
    return plain.encode("utf-8")[:72]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_to_bytes(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bytes(plain), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str | int) -> str:
    """subject(=user id)を sub に入れたアクセストークンを発行。有効期限60分。"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    """検証して sub(user id文字列)を返す。失敗時 None。"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except JWTError:
        return None
