from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._types import pg_enum
from app.models.enums import ProjectStatus


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    client_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    required_skills: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    unit_price_min: Mapped[int | None] = mapped_column(Integer)
    unit_price_max: Mapped[int | None] = mapped_column(Integer)
    headcount: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    work_location: Mapped[str | None] = mapped_column(String(200))
    remote_ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    start_date: Mapped[date | None] = mapped_column()
    status: Mapped[ProjectStatus] = mapped_column(
        pg_enum(ProjectStatus, "project_status"),
        nullable=False,
        default=ProjectStatus.募集中,
    )
    note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
