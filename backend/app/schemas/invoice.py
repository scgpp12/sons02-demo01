from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import InvoiceStatus


class InvoiceBase(BaseModel):
    contract_id: int
    year_month: date
    billed_amount: int = 0
    status: InvoiceStatus = InvoiceStatus.未請求
    issued_date: date | None = None


class InvoiceUpdate(BaseModel):
    """請求はステータスと発行日のみ手動更新可。金額は自動計算で更新する。"""

    status: InvoiceStatus | None = None
    issued_date: date | None = None


class InvoiceRead(InvoiceBase):
    id: int
    engineer_name: str | None = None
    counterparty_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvoiceGenerateRequest(BaseModel):
    """対象月の請求を稼働実績から一括生成/再計算する。"""

    year_month: date
