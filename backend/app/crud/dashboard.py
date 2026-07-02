"""ダッシュボード集計（DBバインド）。"""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.crud.gross_profit import gross_profit_rows
from app.models.client import Client
from app.models.contract import Contract
from app.models.engineer import Engineer
from app.models.enums import ContractStatus, EngineerStatus
from app.schemas.dashboard import (
    DashboardSummary,
    MonthlyRevenue,
    RenewalAlert,
    StatusCount,
)


def _month_start(d: date) -> date:
    return d.replace(day=1)


def _add_months(d: date, n: int) -> date:
    m = d.month - 1 + n
    y = d.year + m // 12
    return date(y, m % 12 + 1, 1)


def build_summary(db: Session, today: date, trend_months: int = 6) -> DashboardSummary:
    # 技術者ステータス内訳
    status_rows = db.execute(
        select(Engineer.status, func.count()).group_by(Engineer.status)
    ).all()
    breakdown = [StatusCount(status=s.value, count=c) for s, c in status_rows]
    total = sum(c for _, c in status_rows)
    working = next((c for s, c in status_rows if s == EngineerStatus.稼働中), 0)
    waiting = next((c for s, c in status_rows if s == EngineerStatus.待機), 0)
    utilization = round(working / total * 100, 1) if total else 0.0

    # 月次トレンド（直近 trend_months ヶ月）
    this_month = _month_start(today)
    trend: list[MonthlyRevenue] = []
    for i in range(trend_months - 1, -1, -1):
        ym = _add_months(this_month, -i)
        rows = gross_profit_rows(db, ym)
        revenue = sum(r.upper_billed for r in rows)
        cost = sum(r.lower_paid for r in rows)
        trend.append(
            MonthlyRevenue(year_month=ym, revenue=revenue, cost=cost, gross_profit=revenue - cost)
        )

    this = trend[-1] if trend else MonthlyRevenue(
        year_month=this_month, revenue=0, cost=0, gross_profit=0
    )
    margin = round(this.gross_profit / this.revenue * 100, 1) if this.revenue else None

    # 更新待ちアラート（end_date が当月から1ヶ月以内 & 契約中）
    horizon = _add_months(this_month, 1)
    alerts_q = db.execute(
        select(Contract, Engineer, Client)
        .join(Engineer, Engineer.id == Contract.engineer_id)
        .outerjoin(Client, Client.id == Contract.counterparty_client_id)
        .where(Contract.status == ContractStatus.契約中)
        .where(Contract.end_date <= horizon)
        .order_by(Contract.end_date)
    ).all()
    alerts = [
        RenewalAlert(
            contract_id=c.id,
            engineer_name=e.name,
            counterparty_name=cl.company_name if cl else None,
            end_date=c.end_date,
            days_left=(c.end_date - today).days,
        )
        for c, e, cl in alerts_q
    ]

    return DashboardSummary(
        total_engineers=total,
        working_count=working,
        waiting_count=waiting,
        utilization_rate=utilization,
        engineer_status_breakdown=breakdown,
        this_month_revenue=this.revenue,
        this_month_gross_profit=this.gross_profit,
        this_month_gross_margin=margin,
        monthly_trend=trend,
        renewal_alerts=alerts,
    )
