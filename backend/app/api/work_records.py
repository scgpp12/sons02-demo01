from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, DbDep
from app.models.contract import Contract
from app.models.engineer import Engineer
from app.models.work_record import WorkRecord
from app.schemas.common import Page
from app.schemas.work_record import WorkRecordCreate, WorkRecordRead, WorkRecordUpdate

router = APIRouter(prefix="/work-records", tags=["work-records"])


def _enrich(db: Session, wr: WorkRecord) -> WorkRecordRead:
    out = WorkRecordRead.model_validate(wr)
    c = db.get(Contract, wr.contract_id)
    if c:
        e = db.get(Engineer, c.engineer_id)
        out.engineer_name = e.name if e else None
    return out


@router.get("", response_model=Page[WorkRecordRead])
def list_work_records(
    db: DbDep,
    _: CurrentUser,
    contract_id: int | None = None,
    year_month: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> Page[WorkRecordRead]:
    stmt = select(WorkRecord)
    if contract_id:
        stmt = stmt.where(WorkRecord.contract_id == contract_id)
    if year_month:
        stmt = stmt.where(WorkRecord.year_month == year_month.replace(day=1))

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    stmt = (
        stmt.order_by(WorkRecord.year_month.desc(), WorkRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [_enrich(db, wr) for wr in db.execute(stmt).scalars().all()]
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=WorkRecordRead, status_code=status.HTTP_201_CREATED)
def upsert_work_record(
    payload: WorkRecordCreate, db: DbDep, _: CurrentUser
) -> WorkRecordRead:
    """契約×対象月で upsert（グリッド入力用）。既存があれば稼働時間を更新。"""
    if db.get(Contract, payload.contract_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "契約が見つかりません")
    ym = payload.year_month.replace(day=1)
    existing = db.execute(
        select(WorkRecord).where(
            WorkRecord.contract_id == payload.contract_id, WorkRecord.year_month == ym
        )
    ).scalar_one_or_none()
    if existing:
        existing.worked_hours = payload.worked_hours
        db.commit()
        db.refresh(existing)
        return _enrich(db, existing)
    wr = WorkRecord(
        contract_id=payload.contract_id, year_month=ym, worked_hours=payload.worked_hours
    )
    db.add(wr)
    db.commit()
    db.refresh(wr)
    return _enrich(db, wr)


@router.put("/{record_id}", response_model=WorkRecordRead)
def update_work_record(
    record_id: int, payload: WorkRecordUpdate, db: DbDep, _: CurrentUser
) -> WorkRecordRead:
    wr = db.get(WorkRecord, record_id)
    if wr is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "稼働実績が見つかりません")
    wr.worked_hours = payload.worked_hours
    db.commit()
    db.refresh(wr)
    return _enrich(db, wr)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_record(record_id: int, db: DbDep, _: CurrentUser) -> None:
    wr = db.get(WorkRecord, record_id)
    if wr is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "稼働実績が見つかりません")
    db.delete(wr)
    db.commit()
