from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.core.deps import CurrentUser, DbDep, ensure_can_edit
from app.crud.base import CRUDBase
from app.models.client import Client
from app.models.enums import BusinessType
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from app.schemas.common import Page

router = APIRouter(prefix="/clients", tags=["clients"])
crud = CRUDBase(Client)


@router.get("", response_model=Page[ClientRead])
def list_clients(
    db: DbDep,
    _: CurrentUser,
    q: str | None = Query(None, description="会社名・担当者名の部分一致"),
    business_type: BusinessType | None = None,
    can_distribute: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Page[ClientRead]:
    stmt = select(Client)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Client.company_name.ilike(like) | Client.contact_name.ilike(like))
    if business_type:
        stmt = stmt.where(Client.business_type == business_type)
    if can_distribute is not None:
        stmt = stmt.where(Client.can_distribute == can_distribute)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    stmt = stmt.order_by(Client.id.desc()).offset((page - 1) * page_size).limit(page_size)
    items = db.execute(stmt).scalars().all()
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: int, db: DbDep, _: CurrentUser) -> Client:
    obj = crud.get(db, client_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "取引先が見つかりません")
    return obj


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(payload: ClientCreate, db: DbDep, user: CurrentUser) -> Client:
    data = payload.model_dump()
    data["created_by"] = user.id
    return crud.create(db, data)


@router.put("/{client_id}", response_model=ClientRead)
def update_client(
    client_id: int, payload: ClientUpdate, db: DbDep, user: CurrentUser
) -> Client:
    obj = crud.get(db, client_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "取引先が見つかりません")
    ensure_can_edit(user, obj.created_by)
    return crud.update(db, obj, payload.model_dump(exclude_unset=True))


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: DbDep, user: CurrentUser) -> None:
    obj = crud.get(db, client_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "取引先が見つかりません")
    ensure_can_edit(user, obj.created_by)
    crud.delete(db, obj)
