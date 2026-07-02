"""請求の自動生成・再計算（DBバインド）。計算式は billing.py の純粋関数を使う。"""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.billing import BillingTerms, calc_billed_amount
from app.models.contract import Contract
from app.models.enums import ContractType, InvoiceStatus
from app.models.invoice import Invoice
from app.models.work_record import WorkRecord


def _terms_of(contract: Contract) -> BillingTerms:
    return BillingTerms(
        unit_price=contract.unit_price,
        settlement_lower=contract.settlement_lower,
        settlement_upper=contract.settlement_upper,
        overtime_rate=contract.overtime_rate or 0,
        deduction_rate=contract.deduction_rate or 0,
    )


def generate_invoices_for_month(db: Session, year_month: date) -> list[Invoice]:
    """対象月の稼働実績から、上位契約の請求を生成/再計算する。

    - 上位契約(contract_type=上位)で、対象月の稼働実績があるものが対象。
    - 既存の請求があれば billed_amount を再計算（status=未請求のもののみ更新）。
    - 請求済/入金済の請求は金額を上書きしない（確定後の改変を防ぐ）。
    """
    ym = year_month.replace(day=1)

    # 対象月の稼働実績を契約ごとに引く（上位契約のみ）
    stmt = (
        select(WorkRecord, Contract)
        .join(Contract, Contract.id == WorkRecord.contract_id)
        .where(WorkRecord.year_month == ym)
        .where(Contract.contract_type == ContractType.上位)
    )
    rows = db.execute(stmt).all()

    result: list[Invoice] = []
    for wr, contract in rows:
        amount = calc_billed_amount(_terms_of(contract), wr.worked_hours)

        existing = db.execute(
            select(Invoice).where(
                Invoice.contract_id == contract.id, Invoice.year_month == ym
            )
        ).scalar_one_or_none()

        if existing is None:
            inv = Invoice(
                contract_id=contract.id,
                year_month=ym,
                billed_amount=amount,
                status=InvoiceStatus.未請求,
            )
            db.add(inv)
            result.append(inv)
        elif existing.status == InvoiceStatus.未請求:
            existing.billed_amount = amount
            result.append(existing)
        else:
            # 確定済みは触らない
            result.append(existing)

    db.commit()
    for inv in result:
        db.refresh(inv)
    return result
