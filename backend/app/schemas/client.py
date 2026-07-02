from datetime import datetime

from pydantic import BaseModel

from app.models.enums import BusinessType


class ClientBase(BaseModel):
    company_name: str
    business_type: BusinessType
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    can_distribute: bool = True
    note: str | None = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    company_name: str | None = None
    business_type: BusinessType | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    can_distribute: bool | None = None
    note: str | None = None


class ClientRead(ClientBase):
    id: int
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
