from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WorkRecord(Base):
    __tablename__ = "work_records"
    __table_args__ = (
        UniqueConstraint("contract_id", "year_month", name="uq_work_contract_month"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    contract_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False
    )
    # 対象月は月初日(YYYY-MM-01)で格納
    year_month: Mapped[date] = mapped_column(nullable=False)
    worked_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
