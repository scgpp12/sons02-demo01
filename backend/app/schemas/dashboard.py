from datetime import date

from pydantic import BaseModel


class StatusCount(BaseModel):
    status: str
    count: int


class MonthlyRevenue(BaseModel):
    year_month: date
    revenue: int  # 上位契約の請求合計
    cost: int  # 下位契約の支払合計
    gross_profit: int


class RenewalAlert(BaseModel):
    contract_id: int
    engineer_name: str
    counterparty_name: str | None
    end_date: date
    days_left: int


class DashboardSummary(BaseModel):
    total_engineers: int
    working_count: int  # 稼働中
    waiting_count: int  # 待機
    utilization_rate: float  # 稼働率(%)
    engineer_status_breakdown: list[StatusCount]
    this_month_revenue: int
    this_month_gross_profit: int
    this_month_gross_margin: float | None
    monthly_trend: list[MonthlyRevenue]  # 直近数ヶ月
    renewal_alerts: list[RenewalAlert]
