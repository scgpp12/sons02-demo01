"""FastAPI Dependency: current_user の解決とロール制御。"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User

# tokenUrl はSwagger UIのAuthorizeボタン用
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

DbDep = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbDep,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証に失敗しました",
        headers={"WWW-Authenticate": "Bearer"},
    )
    sub = decode_access_token(token)
    if sub is None:
        raise cred_exc
    user = db.get(User, int(sub))
    if user is None or not user.is_active:
        raise cred_exc
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole):
    """指定ロールのみ許可するDependencyを生成。"""

    def checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この操作を行う権限がありません",
            )
        return user

    return checker


# admin専用（ユーザー管理など）
require_admin = require_roles(UserRole.admin)


def can_edit_resource(user: User, created_by: int | None) -> bool:
    """編集権限の共通判定。

    - admin / manager: 何でも編集可
    - sales         : 自分が登録した(created_by==自分)もののみ編集可
    """
    if user.role in (UserRole.admin, UserRole.manager):
        return True
    return created_by is not None and created_by == user.id


def ensure_can_edit(user: User, created_by: int | None) -> None:
    if not can_edit_resource(user, created_by):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="自分が登録したデータのみ編集できます",
        )
