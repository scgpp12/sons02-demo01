from fastapi import APIRouter, Form, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbDep
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.auth import Token, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(db: DbDep, username: str = Form(...), password: str = Form(...)) -> Token:
    """OAuth2 password flow 準拠（username=email）。JWTを返す。

    フロントは email/password を application/x-www-form-urlencoded で送る。
    """
    user = db.execute(select(User).where(User.email == username)).scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="無効なユーザーです")
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(current: CurrentUser) -> User:
    return current
