from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._types import pg_enum
from app.models.enums import BusinessType


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    business_type: Mapped[BusinessType] = mapped_column(
        pg_enum(BusinessType, "business_type"), nullable=False
    )
    contact_name: Mapped[str | None] = mapped_column(String(100))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(30))
    can_distribute: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
