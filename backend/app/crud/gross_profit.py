"""粗利の算出（DBバインド）。上位請求額 − 下位支払額。"""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.billing import BillingTerms, calc_billed_amount, calc_gross_profit
from app.models.contract import Contract
from app.models.engineer import Engineer
from app.models.enums import ContractType
from app.models.work_record import WorkRecord
from app.schemas.contract import GrossProfitRow


def _terms_of(c: Contract) -> BillingTerms:
    return BillingTerms(
        unit_price=c.unit_price,
        settlement_lower=c.settlement_lower,
        settlement_upper=c.settlement_upper,
        overtime_rate=c.overtime_rate or 0,
        deduction_rate=c.deduction_rate or 0,
    )


def _amount_for(db: Session, contract: Contract, ym: date) -> int:
    """対象月の稼働実績があれば実績で、なければ単価で算出。"""
    wr = db.execute(
        select(WorkRecord).where(
            WorkRecord.contract_id == contract.id, WorkRecord.year_month == ym
        )
    ).scalar_one_or_none()
    if wr is None:
        return contract.unit_price
    return calc_billed_amount(_terms_of(contract), wr.worked_hours)


def gross_profit_rows(db: Session, year_month: date) -> list[GrossProfitRow]:
    """対象月の、各上位契約に対する粗利明細を返す。

    上位契約を基点に、その下位契約(parent_contract_id==上位.id)を引いて差額を出す。
    """
    ym = year_month.replace(day=1)

    uppers = db.execute(
        select(Contract).where(Contract.contract_type == ContractType.上位)
    ).scalars().all()

    rows: list[GrossProfitRow] = []
    for up in uppers:
        upper_billed = _amount_for(db, up, ym)

        # 1上位に複数の下位が紐づき得るため全件を合算する（PRE-05対応）
        lowers = db.execute(
            select(Contract).where(
                Contract.parent_contract_id == up.id,
                Contract.contract_type == ContractType.下位,
            )
        ).scalars().all()
        lower_paid = sum(_amount_for(db, low, ym) for low in lowers)

        profit, margin = calc_gross_profit(upper_billed, lower_paid)
        eng = db.get(Engineer, up.engineer_id)
        rows.append(
            GrossProfitRow(
                engineer_id=up.engineer_id,
                engineer_name=eng.name if eng else "",
                year_month=ym,
                # 下位がちょうど1件のときのみID、0件はNone、複数件もNone（合算のため）
                lower_contract_id=lowers[0].id if len(lowers) == 1 else None,
                lower_count=len(lowers),
                upper_contract_id=up.id,
                upper_billed=upper_billed,
                lower_paid=lower_paid,
                gross_profit=profit,
                gross_margin=margin,
            )
        )
    return rows
