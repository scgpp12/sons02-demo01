from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._types import pg_enum
from app.models.enums import ContractStatus, ContractType


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    engineer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("engineers.id", ondelete="RESTRICT"), nullable=False
    )
    project_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="SET NULL")
    )
    contract_type: Mapped[ContractType] = mapped_column(
        pg_enum(ContractType, "contract_type"), nullable=False
    )
    counterparty_client_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("clients.id", ondelete="RESTRICT")
    )
    # 下位契約 → 紐づく上位契約 への自己参照
    parent_contract_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("contracts.id", ondelete="SET NULL")
    )
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    settlement_lower: Mapped[int | None] = mapped_column(Integer)
    settlement_upper: Mapped[int | None] = mapped_column(Integer)
    overtime_rate: Mapped[int] = mapped_column(Integer, default=0)
    deduction_rate: Mapped[int] = mapped_column(Integer, default=0)
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date] = mapped_column(nullable=False)
    auto_renew: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[ContractStatus] = mapped_column(
        pg_enum(ContractStatus, "contract_status"),
        nullable=False,
        default=ContractStatus.契約中,
    )
    contract_file_path: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
