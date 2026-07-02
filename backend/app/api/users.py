from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from app.core.deps import DbDep, require_admin
from app.core.security import hash_password
from app.models.user import User
from app.schemas.common import Page
from app.schemas.user import UserCreate, UserRead, UserUpdate

# ユーザー管理は admin 専用
router = APIRouter(
    prefix="/users", tags=["users"], dependencies=[Depends(require_admin)]
)
AdminUser = Annotated[User, Depends(require_admin)]


@router.get("", response_model=Page[UserRead])
def list_users(
    db: DbDep,
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Page[UserRead]:
    stmt = select(User)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(User.name.ilike(like) | User.email.ilike(like))
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    stmt = stmt.order_by(User.id).offset((page - 1) * page_size).limit(page_size)
    items = db.execute(stmt).scalars().all()
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: DbDep) -> User:
    exists = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "このメールアドレスは既に使われています")
    user = User(
        email=payload.email,
        name=payload.name,
        role=payload.role,
        is_active=payload.is_active,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, db: DbDep) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ユーザーが見つかりません")
    data = payload.model_dump(exclude_unset=True)
    pw = data.pop("password", None)
    if pw:
        user.password_hash = hash_password(pw)
    for k, v in data.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: DbDep) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ユーザーが見つかりません")
    db.delete(user)
    db.commit()
