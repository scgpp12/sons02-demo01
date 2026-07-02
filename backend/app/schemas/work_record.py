from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator


class WorkRecordBase(BaseModel):
    contract_id: int
    year_month: date  # 月初日(YYYY-MM-01)で扱う
    worked_hours: Decimal

    @field_validator("year_month")
    @classmethod
    def _normalize_month(cls, v: date) -> date:
        """対象月は必ず月初日に正規化。"""
        return v.replace(day=1)


class WorkRecordCreate(WorkRecordBase):
    pass


class WorkRecordUpdate(BaseModel):
    worked_hours: Decimal


class WorkRecordRead(WorkRecordBase):
    id: int
    engineer_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
