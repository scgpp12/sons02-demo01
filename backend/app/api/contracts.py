from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, DbDep, require_roles
from app.crud.base import CRUDBase
from app.crud.gross_profit import gross_profit_rows
from app.models.client import Client
from app.models.contract import Contract
from app.models.engineer import Engineer
from app.models.enums import ContractStatus, ContractType, UserRole
from app.models.project import Project
from app.schemas.common import Page
from app.schemas.contract import (
    ContractCreate,
    ContractRead,
    ContractUpdate,
    GrossProfitRow,
)

router = APIRouter(prefix="/contracts", tags=["contracts"])
crud = CRUDBase(Contract)

# 契約は admin/manager のみ編集可（sales は閲覧のみ）
Editor = Annotated[object, Depends(require_roles(UserRole.admin, UserRole.manager))]


def _enrich(db: Session, c: Contract) -> ContractRead:
    out = ContractRead.model_validate(c)
    eng = db.get(Engineer, c.engineer_id)
    out.engineer_name = eng.name if eng else None
    if c.counterparty_client_id:
        cl = db.get(Client, c.counterparty_client_id)
        out.counterparty_name = cl.company_name if cl else None
    if c.project_id:
        pj = db.get(Project, c.project_id)
        out.project_title = pj.title if pj else None
    return out


@router.get("", response_model=Page[ContractRead])
def list_contracts(
    db: DbDep,
    _: CurrentUser,
    engineer_id: int | None = None,
    contract_type: ContractType | None = None,
    status_: ContractStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Page[ContractRead]:
    stmt = select(Contract)
    if engineer_id:
        stmt = stmt.where(Contract.engineer_id == engineer_id)
    if contract_type:
        stmt = stmt.where(Contract.contract_type == contract_type)
    if status_:
        stmt = stmt.where(Contract.status == status_)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    stmt = stmt.order_by(Contract.id.desc()).offset((page - 1) * page_size).limit(page_size)
    items = [_enrich(db, c) for c in db.execute(stmt).scalars().all()]
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/renewals", response_model=list[ContractRead])
def list_renewals(db: DbDep, _: CurrentUser, today: date | None = None) -> list[ContractRead]:
    """end_date が当月から1ヶ月以内 かつ status=契約中 の契約を抽出。"""
    base = today or date.today()
    month_start = base.replace(day=1)
    # 1ヶ月後の月初
    m = month_start.month - 1 + 1
    horizon = date(month_start.year + m // 12, m % 12 + 1, 1)
    rows = (
        db.execute(
            select(Contract)
            .where(Contract.status == ContractStatus.契約中)
            .where(Contract.end_date <= horizon)
            .order_by(Contract.end_date)
        )
        .scalars()
        .all()
    )
    return [_enrich(db, c) for c in rows]


@router.get("/gross-profit", response_model=list[GrossProfitRow])
def list_gross_profit(
    db: DbDep, _: CurrentUser, year_month: date
) -> list[GrossProfitRow]:
    """対象月の技術者別 粗利明細。"""
    return gross_profit_rows(db, year_month)


@router.get("/uppers", response_model=list[ContractRead])
def list_upper_contracts(db: DbDep, _: CurrentUser) -> list[ContractRead]:
    """下位契約の紐づけ用：上位契約の一覧。"""
    rows = (
        db.execute(select(Contract).where(Contract.contract_type == ContractType.上位))
        .scalars()
        .all()
    )
    return [_enrich(db, c) for c in rows]


@router.get("/{contract_id}", response_model=ContractRead)
def get_contract(contract_id: int, db: DbDep, _: CurrentUser) -> ContractRead:
    obj = crud.get(db, contract_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "契約が見つかりません")
    return _enrich(db, obj)


@router.post("", response_model=ContractRead, status_code=status.HTTP_201_CREATED)
def create_contract(payload: ContractCreate, db: DbDep, _: Editor) -> ContractRead:
    obj = crud.create(db, payload.model_dump())
    return _enrich(db, obj)


@router.put("/{contract_id}", response_model=ContractRead)
def update_contract(
    contract_id: int, payload: ContractUpdate, db: DbDep, _: Editor
) -> ContractRead:
    obj = crud.get(db, contract_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "契約が見つかりません")
    obj = crud.update(db, obj, payload.model_dump(exclude_unset=True))
    return _enrich(db, obj)


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(contract_id: int, db: DbDep, _: Editor) -> None:
    obj = crud.get(db, contract_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "契約が見つかりません")
    crud.delete(db, obj)
