from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, DbDep
from app.crud.invoice import generate_invoices_for_month
from app.models.client import Client
from app.models.contract import Contract
from app.models.engineer import Engineer
from app.models.enums import InvoiceStatus
from app.models.invoice import Invoice
from app.schemas.common import Page
from app.schemas.invoice import (
    InvoiceGenerateRequest,
    InvoiceRead,
    InvoiceUpdate,
)

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _enrich(db: Session, inv: Invoice) -> InvoiceRead:
    out = InvoiceRead.model_validate(inv)
    c = db.get(Contract, inv.contract_id)
    if c:
        e = db.get(Engineer, c.engineer_id)
        out.engineer_name = e.name if e else None
        if c.counterparty_client_id:
            cl = db.get(Client, c.counterparty_client_id)
            out.counterparty_name = cl.company_name if cl else None
    return out


@router.get("", response_model=Page[InvoiceRead])
def list_invoices(
    db: DbDep,
    _: CurrentUser,
    status_: InvoiceStatus | None = Query(None, alias="status"),
    year_month: date | None = None,
    contract_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Page[InvoiceRead]:
    stmt = select(Invoice)
    if status_:
        stmt = stmt.where(Invoice.status == status_)
    if year_month:
        stmt = stmt.where(Invoice.year_month == year_month.replace(day=1))
    if contract_id:
        stmt = stmt.where(Invoice.contract_id == contract_id)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    stmt = (
        stmt.order_by(Invoice.year_month.desc(), Invoice.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [_enrich(db, inv) for inv in db.execute(stmt).scalars().all()]
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.post("/generate", response_model=list[InvoiceRead])
def generate_invoices(
    payload: InvoiceGenerateRequest, db: DbDep, _: CurrentUser
) -> list[InvoiceRead]:
    """対象月の稼働実績から請求を一括生成/再計算する（金額は自動計算）。"""
    invoices = generate_invoices_for_month(db, payload.year_month)
    return [_enrich(db, inv) for inv in invoices]


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(invoice_id: int, db: DbDep, _: CurrentUser) -> InvoiceRead:
    inv = db.get(Invoice, invoice_id)
    if inv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "請求が見つかりません")
    return _enrich(db, inv)


@router.put("/{invoice_id}", response_model=InvoiceRead)
def update_invoice(
    invoice_id: int, payload: InvoiceUpdate, db: DbDep, _: CurrentUser
) -> InvoiceRead:
    """ステータス・発行日の手動更新。金額は generate で再計算する。"""
    inv = db.get(Invoice, invoice_id)
    if inv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "請求が見つかりません")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(inv, k, v)
    db.commit()
    db.refresh(inv)
    return _enrich(db, inv)
