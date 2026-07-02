from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import ContractStatus, ContractType


class ContractBase(BaseModel):
    engineer_id: int
    project_id: int | None = None
    contract_type: ContractType
    counterparty_client_id: int | None = None
    parent_contract_id: int | None = None
    unit_price: int
    settlement_lower: int | None = None
    settlement_upper: int | None = None
    overtime_rate: int = 0
    deduction_rate: int = 0
    start_date: date
    end_date: date
    auto_renew: bool = False
    status: ContractStatus = ContractStatus.契約中
    contract_file_path: str | None = None


class ContractCreate(ContractBase):
    pass


class ContractUpdate(BaseModel):
    engineer_id: int | None = None
    project_id: int | None = None
    contract_type: ContractType | None = None
    counterparty_client_id: int | None = None
    parent_contract_id: int | None = None
    unit_price: int | None = None
    settlement_lower: int | None = None
    settlement_upper: int | None = None
    overtime_rate: int | None = None
    deduction_rate: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    auto_renew: bool | None = None
    status: ContractStatus | None = None
    contract_file_path: str | None = None


class ContractRead(ContractBase):
    id: int
    engineer_name: str | None = None
    counterparty_name: str | None = None
    project_title: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GrossProfitRow(BaseModel):
    """技術者×対象月の粗利明細。"""

    engineer_id: int
    engineer_name: str
    year_month: date
    upper_contract_id: int | None
    lower_contract_id: int | None  # 下位がちょうど1件のときのみ。0件/複数件はNull
    lower_count: int = 0  # 紐づく下位契約の件数
    upper_billed: int
    lower_paid: int
    gross_profit: int
    gross_margin: float | None
