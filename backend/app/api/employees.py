from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from app.core.crypto import encrypt
from app.core.deps import CurrentUser, DbDep, require_roles
from app.models.employee import (
    Employee,
    EmployeeBankAccount,
    EmployeeDocument,
    EmployeeEmergencyContact,
    EmployeeEmploymentHistory,
    EmployeeMyNumber,
    EmployeeResidenceCard,
)
from app.models.enums import EmployeeStatus, UserRole
from app.schemas.common import Page
from app.schemas.employee import (
    BankAccountCreate,
    BankAccountRead,
    DocumentCreate,
    DocumentRead,
    EmergencyContactCreate,
    EmergencyContactRead,
    EmployeeCreate,
    EmployeeDetail,
    EmployeeRead,
    EmployeeUpdate,
    EmploymentHistoryCreate,
    EmploymentHistoryRead,
    MyNumberRead,
    MyNumberUpsert,
    ResidenceCardCreate,
    ResidenceCardRead,
)

# 社員個人情報（社員本体/在留カード/銀行口座/緊急連絡先/転職情報/提出書類/マイナンバー）は
# 最高機密。閲覧・編集とも admin / manager に限定し、sales からの越境を遮断する（OUT-08 是正）。
# ルータ単位で require_roles を掛けるので、配下の全エンドポイントに自動適用される。
router = APIRouter(
    prefix="/employees",
    tags=["employees"],
    dependencies=[Depends(require_roles(UserRole.admin, UserRole.manager))],
)


def _get_employee(db: DbDep, employee_id: int) -> Employee:
    emp = db.get(Employee, employee_id)
    if emp is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "社員が見つかりません")
    return emp


# ============== 社員本体 ==============
@router.get("", response_model=Page[EmployeeRead])
def list_employees(
    db: DbDep,
    _: CurrentUser,
    q: str | None = Query(None, description="氏名・カナ・ローマ字の部分一致"),
    status_: EmployeeStatus | None = Query(None, alias="status"),
    nationality: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Page[EmployeeRead]:
    stmt = select(Employee)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            Employee.name.ilike(like)
            | Employee.name_kana.ilike(like)
            | Employee.name_romaji.ilike(like)
        )
    if status_:
        stmt = stmt.where(Employee.status == status_)
    if nationality:
        stmt = stmt.where(Employee.nationality == nationality)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    stmt = stmt.order_by(Employee.id.desc()).offset((page - 1) * page_size).limit(page_size)
    items = db.execute(stmt).scalars().all()
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/expiring-residence", response_model=list[ResidenceCardRead])
def expiring_residence_cards(
    db: DbDep, _: CurrentUser, within_days: int = Query(90, ge=1, le=365)
) -> list[EmployeeResidenceCard]:
    """在留期限が within_days 日以内に切れる現行カードを抽出（更新アラート用）。"""
    limit = date.fromordinal(date.today().toordinal() + within_days)
    rows = (
        db.execute(
            select(EmployeeResidenceCard)
            .where(EmployeeResidenceCard.is_current.is_(True))
            .where(EmployeeResidenceCard.expiry_date <= limit)
            .order_by(EmployeeResidenceCard.expiry_date)
        )
        .scalars()
        .all()
    )
    return list(rows)


@router.get("/{employee_id}", response_model=EmployeeDetail)
def get_employee(employee_id: int, db: DbDep, _: CurrentUser) -> EmployeeDetail:
    emp = _get_employee(db, employee_id)
    detail = EmployeeDetail.model_validate(emp)
    detail.residence_cards = [
        ResidenceCardRead.model_validate(x)
        for x in db.execute(
            select(EmployeeResidenceCard).where(
                EmployeeResidenceCard.employee_id == employee_id
            )
        ).scalars()
    ]
    detail.bank_accounts = [
        BankAccountRead.model_validate(x)
        for x in db.execute(
            select(EmployeeBankAccount).where(EmployeeBankAccount.employee_id == employee_id)
        ).scalars()
    ]
    detail.emergency_contacts = [
        EmergencyContactRead.model_validate(x)
        for x in db.execute(
            select(EmployeeEmergencyContact).where(
                EmployeeEmergencyContact.employee_id == employee_id
            )
        ).scalars()
    ]
    detail.employment_history = [
        EmploymentHistoryRead.model_validate(x)
        for x in db.execute(
            select(EmployeeEmploymentHistory).where(
                EmployeeEmploymentHistory.employee_id == employee_id
            )
        ).scalars()
    ]
    detail.documents = [
        DocumentRead.model_validate(x)
        for x in db.execute(
            select(EmployeeDocument).where(EmployeeDocument.employee_id == employee_id)
        ).scalars()
    ]
    mn = db.get(EmployeeMyNumber, employee_id)
    if mn:
        detail.my_number = MyNumberRead(
            has_card=mn.has_card,
            collected_at=mn.collected_at,
            has_number=bool(mn.my_number_enc),
        )
    return detail


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: DbDep, _: CurrentUser) -> Employee:
    emp = Employee(**payload.model_dump())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


@router.put("/{employee_id}", response_model=EmployeeRead)
def update_employee(
    employee_id: int, payload: EmployeeUpdate, db: DbDep, _: CurrentUser
) -> Employee:
    emp = _get_employee(db, employee_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(emp, k, v)
    db.commit()
    db.refresh(emp)
    return emp


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: int, db: DbDep, _: CurrentUser) -> None:
    emp = _get_employee(db, employee_id)
    db.delete(emp)
    db.commit()


# ============== 在留カード ==============
@router.post(
    "/{employee_id}/residence-cards",
    response_model=ResidenceCardRead,
    status_code=status.HTTP_201_CREATED,
)
def add_residence_card(
    employee_id: int, payload: ResidenceCardCreate, db: DbDep, _: CurrentUser
) -> EmployeeResidenceCard:
    _get_employee(db, employee_id)
    obj = EmployeeResidenceCard(employee_id=employee_id, **payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/{employee_id}/residence-cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_residence_card(
    employee_id: int, card_id: int, db: DbDep, _: CurrentUser
) -> None:
    obj = db.get(EmployeeResidenceCard, card_id)
    if obj is None or obj.employee_id != employee_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "在留カードが見つかりません")
    db.delete(obj)
    db.commit()


# ============== 銀行口座 ==============
@router.post(
    "/{employee_id}/bank-accounts",
    response_model=BankAccountRead,
    status_code=status.HTTP_201_CREATED,
)
def add_bank_account(
    employee_id: int, payload: BankAccountCreate, db: DbDep, _: CurrentUser
) -> EmployeeBankAccount:
    _get_employee(db, employee_id)
    obj = EmployeeBankAccount(employee_id=employee_id, **payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/{employee_id}/bank-accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_bank_account(
    employee_id: int, account_id: int, db: DbDep, _: CurrentUser
) -> None:
    obj = db.get(EmployeeBankAccount, account_id)
    if obj is None or obj.employee_id != employee_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "口座が見つかりません")
    db.delete(obj)
    db.commit()


# ============== 緊急連絡先 ==============
@router.post(
    "/{employee_id}/emergency-contacts",
    response_model=EmergencyContactRead,
    status_code=status.HTTP_201_CREATED,
)
def add_emergency_contact(
    employee_id: int, payload: EmergencyContactCreate, db: DbDep, _: CurrentUser
) -> EmployeeEmergencyContact:
    _get_employee(db, employee_id)
    obj = EmployeeEmergencyContact(employee_id=employee_id, **payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/{employee_id}/emergency-contacts/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_emergency_contact(
    employee_id: int, contact_id: int, db: DbDep, _: CurrentUser
) -> None:
    obj = db.get(EmployeeEmergencyContact, contact_id)
    if obj is None or obj.employee_id != employee_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "緊急連絡先が見つかりません")
    db.delete(obj)
    db.commit()


# ============== 転職情報 ==============
@router.post(
    "/{employee_id}/employment-history",
    response_model=EmploymentHistoryRead,
    status_code=status.HTTP_201_CREATED,
)
def add_employment_history(
    employee_id: int, payload: EmploymentHistoryCreate, db: DbDep, _: CurrentUser
) -> EmployeeEmploymentHistory:
    _get_employee(db, employee_id)
    obj = EmployeeEmploymentHistory(employee_id=employee_id, **payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/{employee_id}/employment-history/{history_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_employment_history(
    employee_id: int, history_id: int, db: DbDep, _: CurrentUser
) -> None:
    obj = db.get(EmployeeEmploymentHistory, history_id)
    if obj is None or obj.employee_id != employee_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "転職情報が見つかりません")
    db.delete(obj)
    db.commit()


# ============== 提出書類 ==============
@router.post(
    "/{employee_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def add_document(
    employee_id: int, payload: DocumentCreate, db: DbDep, user: CurrentUser
) -> EmployeeDocument:
    _get_employee(db, employee_id)
    obj = EmployeeDocument(
        employee_id=employee_id, uploaded_by=user.id, **payload.model_dump()
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/{employee_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_document(
    employee_id: int, document_id: int, db: DbDep, _: CurrentUser
) -> None:
    obj = db.get(EmployeeDocument, document_id)
    if obj is None or obj.employee_id != employee_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "書類が見つかりません")
    db.delete(obj)
    db.commit()


# ============== マイナンバー（最高機密） ==============
@router.get("/{employee_id}/my-number", response_model=MyNumberRead)
def get_my_number(employee_id: int, db: DbDep, _: CurrentUser) -> MyNumberRead:
    """平文は返さない。登録有無とカード所持・回収日のみ。"""
    _get_employee(db, employee_id)
    mn = db.get(EmployeeMyNumber, employee_id)
    if mn is None:
        return MyNumberRead(has_card=False, collected_at=None, has_number=False)
    return MyNumberRead(
        has_card=mn.has_card, collected_at=mn.collected_at, has_number=bool(mn.my_number_enc)
    )


@router.put("/{employee_id}/my-number", response_model=MyNumberRead)
def upsert_my_number(
    employee_id: int, payload: MyNumberUpsert, db: DbDep, _: CurrentUser
) -> MyNumberRead:
    """平文の12桁を受け取り暗号化して保存。my_number 未指定なら値は据え置き。"""
    _get_employee(db, employee_id)
    mn = db.get(EmployeeMyNumber, employee_id)
    if mn is None:
        mn = EmployeeMyNumber(employee_id=employee_id)
        db.add(mn)
    mn.has_card = payload.has_card
    mn.collected_at = payload.collected_at
    if payload.my_number is not None:
        mn.my_number_enc = encrypt(payload.my_number) if payload.my_number else None
    db.commit()
    db.refresh(mn)
    return MyNumberRead(
        has_card=mn.has_card, collected_at=mn.collected_at, has_number=bool(mn.my_number_enc)
    )
