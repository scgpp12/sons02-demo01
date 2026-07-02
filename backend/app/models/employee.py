"""社員入社情報（自社雇用の従業員）。要員(engineers)とは別概念。

個人情報保護のため、マイナンバー・銀行・在留カード等は別テーブルに分離。
"""
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._types import pg_enum
from app.models.enums import (
    DocumentKind,
    EmergencyContactKind,
    EmployeeStatus,
    GenderType,
)


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_romaji: Mapped[str] = mapped_column(String(150), nullable=False)
    name_kana: Mapped[str] = mapped_column(String(150), nullable=False)
    birth_date: Mapped[date] = mapped_column(nullable=False)
    gender: Mapped[GenderType | None] = mapped_column(pg_enum(GenderType, "gender_type"))
    nationality: Mapped[str] = mapped_column(String(80), nullable=False)
    mobile_phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    postal_code: Mapped[str | None] = mapped_column(String(8))
    address: Mapped[str | None] = mapped_column(String(300))
    hire_date: Mapped[date | None] = mapped_column()
    status: Mapped[EmployeeStatus] = mapped_column(
        pg_enum(EmployeeStatus, "employee_status"),
        nullable=False,
        default=EmployeeStatus.在籍,
    )
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class EmployeeResidenceCard(Base):
    """在留カード（更新履歴で1:N）。"""

    __tablename__ = "employee_residence_cards"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    residence_status: Mapped[str] = mapped_column(String(100), nullable=False)
    card_number: Mapped[str] = mapped_column(String(20), nullable=False)
    period_text: Mapped[str | None] = mapped_column(String(20))
    expiry_date: Mapped[date] = mapped_column(nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class EmployeeBankAccount(Base):
    """銀行口座【高機密】。"""

    __tablename__ = "employee_bank_accounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    bank_code: Mapped[str | None] = mapped_column(String(4))
    bank_name: Mapped[str | None] = mapped_column(String(100))
    branch_name: Mapped[str | None] = mapped_column(String(100))
    branch_code: Mapped[str | None] = mapped_column(String(3))
    account_number: Mapped[str | None] = mapped_column(String(7))
    account_holder_kana: Mapped[str | None] = mapped_column(String(150))
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class EmployeeEmergencyContact(Base):
    """緊急連絡先（2人以上）。"""

    __tablename__ = "employee_emergency_contacts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[EmergencyContactKind] = mapped_column(
        pg_enum(EmergencyContactKind, "emergency_contact_kind"), nullable=False
    )
    contact_name: Mapped[str] = mapped_column(String(100), nullable=False)
    relationship: Mapped[str | None] = mapped_column(String(50))
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class EmployeeMyNumber(Base):
    """マイナンバー【最高機密・単独テーブル】。値はアプリ層で暗号化して格納。"""

    __tablename__ = "employee_my_number"

    employee_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True
    )
    my_number_enc: Mapped[str | None] = mapped_column(Text)
    has_card: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    collected_at: Mapped[date | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class EmployeeEmploymentHistory(Base):
    """転職情報（雇用保険・前職・源泉徴収票）。"""

    __tablename__ = "employee_employment_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    employment_insurance_no: Mapped[str | None] = mapped_column(String(20))
    previous_company_name: Mapped[str | None] = mapped_column(String(200))
    has_withholding_slip: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    withholding_year: Mapped[int | None] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class EmployeeDocument(Base):
    """提出書類スキャン（ファイル本体は外部ストレージ、ここはパス＋メタのみ）。"""

    __tablename__ = "employee_documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    doc_kind: Mapped[DocumentKind] = mapped_column(
        pg_enum(DocumentKind, "document_kind"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_name: Mapped[str | None] = mapped_column(String(255))
    uploaded_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(server_default=func.now())
