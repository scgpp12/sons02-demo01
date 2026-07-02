from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole


class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole = UserRole.sales
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = None


class UserRead(UserBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
