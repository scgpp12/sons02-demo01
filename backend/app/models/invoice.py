from datetime import date, datetime

from sqlalchemy import BigInteger, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._types import pg_enum
from app.models.enums import InvoiceStatus


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("contract_id", "year_month", name="uq_invoice_contract_month"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    contract_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("contracts.id", ondelete="RESTRICT"), nullable=False
    )
    year_month: Mapped[date] = mapped_column(nullable=False)
    billed_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[InvoiceStatus] = mapped_column(
        pg_enum(InvoiceStatus, "invoice_status"),
        nullable=False,
        default=InvoiceStatus.未請求,
    )
    issued_date: Mapped[date | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
