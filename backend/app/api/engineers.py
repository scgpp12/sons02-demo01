from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.core.deps import CurrentUser, DbDep, ensure_can_edit
from app.crud.base import CRUDBase
from app.models.engineer import Engineer
from app.models.enums import EngineerStatus
from app.schemas.common import Page
from app.schemas.engineer import EngineerCreate, EngineerRead, EngineerUpdate

router = APIRouter(prefix="/engineers", tags=["engineers"])
crud = CRUDBase(Engineer)


@router.get("", response_model=Page[EngineerRead])
def list_engineers(
    db: DbDep,
    _: CurrentUser,
    q: str | None = Query(None, description="氏名・カナ・メールの部分一致"),
    status_: EngineerStatus | None = Query(None, alias="status"),
    skill: str | None = Query(None, description="保有スキル名で絞り込み"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Page[EngineerRead]:
    stmt = select(Engineer)
    conds: list = []
    if q:
        like = f"%{q}%"
        conds.append(
            Engineer.name.ilike(like)
            | Engineer.name_kana.ilike(like)
            | Engineer.email.ilike(like)
        )
    if status_:
        conds.append(Engineer.status == status_)
    if skill:
        # skills JSONB の [{"name": ...}] に skill を含むか
        conds.append(Engineer.skills.contains([{"name": skill}]))
    for c in conds:
        stmt = stmt.where(c)

    total = db.execute(
        select(func.count()).select_from(stmt.subquery())
    ).scalar_one()
    stmt = stmt.order_by(Engineer.id.desc()).offset((page - 1) * page_size).limit(page_size)
    items = db.execute(stmt).scalars().all()
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{engineer_id}", response_model=EngineerRead)
def get_engineer(engineer_id: int, db: DbDep, _: CurrentUser) -> Engineer:
    obj = crud.get(db, engineer_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "技術者が見つかりません")
    return obj


@router.post("", response_model=EngineerRead, status_code=status.HTTP_201_CREATED)
def create_engineer(payload: EngineerCreate, db: DbDep, user: CurrentUser) -> Engineer:
    # model_dump()はネストしたSkillもdictに直列化するので、そのまま渡せる
    data = payload.model_dump()
    data["created_by"] = user.id
    return crud.create(db, data)


@router.put("/{engineer_id}", response_model=EngineerRead)
def update_engineer(
    engineer_id: int, payload: EngineerUpdate, db: DbDep, user: CurrentUser
) -> Engineer:
    obj = crud.get(db, engineer_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "技術者が見つかりません")
    ensure_can_edit(user, obj.created_by)
    data = payload.model_dump(exclude_unset=True)
    return crud.update(db, obj, data)


@router.delete("/{engineer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_engineer(engineer_id: int, db: DbDep, user: CurrentUser) -> None:
    obj = crud.get(db, engineer_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "技術者が見つかりません")
    ensure_can_edit(user, obj.created_by)
    crud.delete(db, obj)
