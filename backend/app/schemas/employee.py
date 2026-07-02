from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import (
    DocumentKind,
    EmergencyContactKind,
    EmployeeStatus,
    GenderType,
)


# ---------------- 在留カード ----------------
class ResidenceCardBase(BaseModel):
    residence_status: str
    card_number: str
    period_text: str | None = None
    expiry_date: date
    is_current: bool = True


class ResidenceCardCreate(ResidenceCardBase):
    pass


class ResidenceCardRead(ResidenceCardBase):
    id: int
    employee_id: int

    model_config = {"from_attributes": True}


# ---------------- 銀行口座 ----------------
class BankAccountBase(BaseModel):
    bank_code: str | None = None
    bank_name: str | None = None
    branch_name: str | None = None
    branch_code: str | None = None
    account_number: str | None = None
    account_holder_kana: str | None = None
    is_primary: bool = True


class BankAccountCreate(BankAccountBase):
    pass


class BankAccountRead(BankAccountBase):
    id: int
    employee_id: int

    model_config = {"from_attributes": True}


# ---------------- 緊急連絡先 ----------------
class EmergencyContactBase(BaseModel):
    kind: EmergencyContactKind
    contact_name: str
    relationship: str | None = None
    phone: str
    note: str | None = None


class EmergencyContactCreate(EmergencyContactBase):
    pass


class EmergencyContactRead(EmergencyContactBase):
    id: int
    employee_id: int

    model_config = {"from_attributes": True}


# ---------------- マイナンバー ----------------
class MyNumberUpsert(BaseModel):
    """平文の12桁を受け取り、アプリ層で暗号化して格納する。"""

    my_number: str | None = None  # 平文（保存時に暗号化）
    has_card: bool = False
    collected_at: date | None = None


class MyNumberRead(BaseModel):
    has_card: bool
    collected_at: date | None = None
    has_number: bool  # 値が登録済みか（平文は返さない）

    model_config = {"from_attributes": True}


# ---------------- 転職情報 ----------------
class EmploymentHistoryBase(BaseModel):
    employment_insurance_no: str | None = None
    previous_company_name: str | None = None
    has_withholding_slip: bool = False
    withholding_year: int | None = None
    note: str | None = None


class EmploymentHistoryCreate(EmploymentHistoryBase):
    pass


class EmploymentHistoryRead(EmploymentHistoryBase):
    id: int
    employee_id: int

    model_config = {"from_attributes": True}


# ---------------- 提出書類 ----------------
class DocumentBase(BaseModel):
    doc_kind: DocumentKind
    file_path: str
    original_name: str | None = None


class DocumentCreate(DocumentBase):
    pass


class DocumentRead(DocumentBase):
    id: int
    employee_id: int
    uploaded_by: int | None = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


# ---------------- 社員本体 ----------------
class EmployeeBase(BaseModel):
    user_id: int | None = None
    name: str
    name_romaji: str
    name_kana: str
    birth_date: date
    gender: GenderType | None = None
    nationality: str
    mobile_phone: str | None = None
    email: str | None = None
    postal_code: str | None = None
    address: str | None = None
    hire_date: date | None = None
    status: EmployeeStatus = EmployeeStatus.在籍
    note: str | None = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    user_id: int | None = None
    name: str | None = None
    name_romaji: str | None = None
    name_kana: str | None = None
    birth_date: date | None = None
    gender: GenderType | None = None
    nationality: str | None = None
    mobile_phone: str | None = None
    email: str | None = None
    postal_code: str | None = None
    address: str | None = None
    hire_date: date | None = None
    status: EmployeeStatus | None = None
    note: str | None = None


class EmployeeRead(EmployeeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmployeeDetail(EmployeeRead):
    """1社員の全関連情報を集約（マイナンバー値は除く）。"""

    residence_cards: list[ResidenceCardRead] = []
    bank_accounts: list[BankAccountRead] = []
    emergency_contacts: list[EmergencyContactRead] = []
    employment_history: list[EmploymentHistoryRead] = []
    documents: list[DocumentRead] = []
    my_number: MyNumberRead | None = None
