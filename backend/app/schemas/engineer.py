from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import EngineerStatus


class Skill(BaseModel):
    name: str
    years: float


class EngineerBase(BaseModel):
    name: str
    name_kana: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[Skill] = []
    skill_sheet_path: str | None = None
    unit_price: int | None = None
    status: EngineerStatus = EngineerStatus.待機
    available_from: date | None = None
    remote_ok: bool = False
    note: str | None = None


class EngineerCreate(EngineerBase):
    pass


class EngineerUpdate(BaseModel):
    name: str | None = None
    name_kana: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[Skill] | None = None
    skill_sheet_path: str | None = None
    unit_price: int | None = None
    status: EngineerStatus | None = None
    available_from: date | None = None
    remote_ok: bool | None = None
    note: str | None = None


class EngineerRead(EngineerBase):
    id: int
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
