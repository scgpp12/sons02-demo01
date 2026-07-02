from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._types import pg_enum
from app.models.enums import EngineerStatus


class Engineer(Base):
    __tablename__ = "engineers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_kana: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30))
    # [{"name": "Python", "years": 5}]
    skills: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    skill_sheet_path: Mapped[str | None] = mapped_column(String(500))
    unit_price: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[EngineerStatus] = mapped_column(
        pg_enum(EngineerStatus, "engineer_status"),
        nullable=False,
        default=EngineerStatus.待機,
    )
    available_from: Mapped[date | None] = mapped_column()
    remote_ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
