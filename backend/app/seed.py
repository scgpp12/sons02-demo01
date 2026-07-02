"""初期データ投入（冪等）。起動時に entrypoint から実行される。

- 初期adminユーザー（既に存在すればスキップ）
- SEED_DEMO=1 のとき、動作確認用の豊富なデモデータも投入
"""
import os
from datetime import date, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.client import Client
from app.models.contract import Contract
from app.models.employee import (
    Employee,
    EmployeeBankAccount,
    EmployeeEmergencyContact,
    EmployeeResidenceCard,
)
from app.models.engineer import Engineer
from app.models.enums import (
    BusinessType,
    ContractStatus,
    ContractType,
    EmergencyContactKind,
    EmployeeStatus,
    EngineerStatus,
    GenderType,
    InvoiceStatus,
    ProjectStatus,
    UserRole,
)
from app.models.invoice import Invoice
from app.models.project import Project
from app.models.user import User
from app.models.work_record import WorkRecord


def _add_months(d: date, n: int) -> date:
    m = d.month - 1 + n
    return date(d.year + m // 12, m % 12 + 1, 1)


def seed_admin(db) -> User:
    admin = db.execute(
        select(User).where(User.email == settings.admin_email)
    ).scalar_one_or_none()
    if admin:
        print(f"[seed] admin already exists: {settings.admin_email}")
        return admin
    admin = User(
        email=settings.admin_email,
        name=settings.admin_name,
        role=UserRole.admin,
        is_active=True,
        password_hash=hash_password(settings.admin_password),
    )
    db.add(admin)
    db.commit()
    print(f"[seed] admin created: {settings.admin_email} / {settings.admin_password}")
    return admin


def seed_users(db, admin: User) -> dict[str, User]:
    """manager / sales ユーザーを追加。"""
    defs = [
        ("manager@example.com", "マネージャー山本", UserRole.manager, "manager123"),
        ("sales1@example.com", "営業 佐藤", UserRole.sales, "sales123"),
        ("sales2@example.com", "営業 鈴木", UserRole.sales, "sales123"),
    ]
    users = {"admin": admin}
    for email, name, role, pw in defs:
        u = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not u:
            u = User(
                email=email,
                name=name,
                role=role,
                is_active=True,
                password_hash=hash_password(pw),
            )
            db.add(u)
        users[email] = u
    db.commit()
    print("[seed] users (manager/sales) ready")
    return users


def seed_demo(db, users: dict[str, User]) -> None:
    if db.execute(select(Engineer)).first():
        print("[seed] demo data already present, skip")
        return

    sales1 = users["sales1@example.com"].id
    sales2 = users["sales2@example.com"].id

    # ---- 取引先 ----
    clients = [
        Client(company_name="株式会社メガバンクシステムズ", business_type=BusinessType.エンド,
               contact_name="情報システム部 田中", contact_email="tanaka@megabank.example.com",
               can_distribute=False, created_by=sales1),
        Client(company_name="日本SIソリューションズ", business_type=BusinessType.SIer,
               contact_name="営業部 高橋", contact_email="takahashi@nihon-si.example.com",
               created_by=sales1),
        Client(company_name="グローバルコンサルティング", business_type=BusinessType.コンサル,
               contact_name="伊藤", created_by=sales2),
        Client(company_name="協力会社アルファ", business_type=BusinessType.BP,
               contact_name="渡辺", contact_email="watanabe@alpha-bp.example.com",
               created_by=sales1),
        Client(company_name="協力会社ベータ", business_type=BusinessType.BP,
               contact_name="中村", created_by=sales2),
        Client(company_name="フリーランス窓口ガンマ", business_type=BusinessType.BP,
               can_distribute=True, created_by=sales2),
    ]
    db.add_all(clients)
    db.flush()
    end1, sier, _consul, bp_a, bp_b, bp_g = clients

    # ---- 技術者 ----
    engineers = [
        Engineer(name="山田 太郎", name_kana="ヤマダ タロウ",
                 skills=[{"name": "Python", "years": 6}, {"name": "AWS", "years": 4},
                         {"name": "FastAPI", "years": 3}],
                 unit_price=650_000, status=EngineerStatus.稼働中, remote_ok=True,
                 available_from=date(2026, 7, 1), created_by=sales1),
        Engineer(name="佐々木 花子", name_kana="ササキ ハナコ",
                 skills=[{"name": "Java", "years": 8}, {"name": "Spring", "years": 6}],
                 unit_price=700_000, status=EngineerStatus.稼働中, remote_ok=False,
                 created_by=sales1),
        Engineer(name="鈴木 一郎", name_kana="スズキ イチロウ",
                 skills=[{"name": "React", "years": 5}, {"name": "TypeScript", "years": 5}],
                 unit_price=620_000, status=EngineerStatus.稼働中, remote_ok=True,
                 created_by=sales2),
        Engineer(name="田中 美咲", name_kana="タナカ ミサキ",
                 skills=[{"name": "Python", "years": 3}, {"name": "Django", "years": 2}],
                 unit_price=550_000, status=EngineerStatus.待機, remote_ok=True,
                 available_from=date(2026, 7, 1), created_by=sales2),
        Engineer(name="高橋 健", name_kana="タカハシ ケン",
                 skills=[{"name": "Go", "years": 4}, {"name": "Kubernetes", "years": 3}],
                 unit_price=750_000, status=EngineerStatus.待機, remote_ok=True,
                 created_by=sales1),
        Engineer(name="伊藤 大輔", name_kana="イトウ ダイスケ",
                 skills=[{"name": "PHP", "years": 7}, {"name": "Laravel", "years": 5}],
                 unit_price=600_000, status=EngineerStatus.契約終了予定, remote_ok=False,
                 created_by=sales1),
        Engineer(name="渡辺 さくら", name_kana="ワタナベ サクラ",
                 skills=[{"name": "Python", "years": 2}, {"name": "データ分析", "years": 2}],
                 unit_price=500_000, status=EngineerStatus.待機, remote_ok=True,
                 created_by=sales2),
        Engineer(name="中村 翔", name_kana="ナカムラ ショウ",
                 skills=[{"name": "C#", "years": 6}, {"name": ".NET", "years": 6}],
                 unit_price=680_000, status=EngineerStatus.離脱, remote_ok=False,
                 created_by=sales2),
    ]
    db.add_all(engineers)
    db.flush()
    eng_yamada, eng_sasaki, eng_suzuki, _eng_tanaka, _eng_taka, eng_ito, _eng_wata, _eng_naka = (
        engineers
    )

    # ---- 案件 ----
    projects = [
        Project(client_id=end1.id, title="勘定系システム保守開発",
                required_skills=[{"name": "Java", "years": 5}],
                unit_price_min=650_000, unit_price_max=800_000, headcount=3,
                work_location="東京都千代田区", remote_ok=False,
                start_date=date(2026, 4, 1), status=ProjectStatus.成約, created_by=sales1),
        Project(client_id=sier.id, title="ECサイトリプレイス（フロント）",
                required_skills=[{"name": "React", "years": 3}],
                unit_price_min=600_000, unit_price_max=700_000, headcount=2,
                work_location="東京都港区", remote_ok=True,
                start_date=date(2026, 5, 1), status=ProjectStatus.成約, created_by=sales2),
        Project(client_id=end1.id, title="データ基盤構築（Python/AWS）",
                required_skills=[{"name": "Python", "years": 4}, {"name": "AWS", "years": 3}],
                unit_price_min=650_000, unit_price_max=780_000, headcount=2,
                remote_ok=True, start_date=date(2026, 7, 1),
                status=ProjectStatus.募集中, created_by=sales1),
        Project(client_id=sier.id, title="社内DX推進PMO",
                required_skills=[{"name": "PM", "years": 5}],
                unit_price_min=700_000, unit_price_max=900_000, headcount=1,
                remote_ok=True, status=ProjectStatus.提案中, created_by=sales2),
    ]
    db.add_all(projects)
    db.flush()
    pj_bank, pj_ec, _pj_data, _pj_pmo = projects

    # ---- 契約（上位/下位ペア）----
    # ペア1: 山田 → エンド(上位) / BPアルファ(下位)
    up1 = Contract(engineer_id=eng_yamada.id, project_id=pj_bank.id,
                   contract_type=ContractType.上位, counterparty_client_id=end1.id,
                   unit_price=750_000, settlement_lower=140, settlement_upper=180,
                   overtime_rate=4_688, deduction_rate=4_688,
                   start_date=date(2026, 4, 1), end_date=date(2026, 9, 30),
                   status=ContractStatus.契約中, auto_renew=True)
    db.add(up1)
    db.flush()
    low1 = Contract(engineer_id=eng_yamada.id, project_id=pj_bank.id,
                    contract_type=ContractType.下位, counterparty_client_id=bp_a.id,
                    parent_contract_id=up1.id,
                    unit_price=650_000, settlement_lower=140, settlement_upper=180,
                    overtime_rate=4_063, deduction_rate=4_063,
                    start_date=date(2026, 4, 1), end_date=date(2026, 9, 30),
                    status=ContractStatus.契約中, auto_renew=True)

    # ペア2: 鈴木 → SIer(上位) / BPベータ(下位)
    up2 = Contract(engineer_id=eng_suzuki.id, project_id=pj_ec.id,
                   contract_type=ContractType.上位, counterparty_client_id=sier.id,
                   unit_price=680_000, settlement_lower=140, settlement_upper=180,
                   overtime_rate=4_250, deduction_rate=4_250,
                   start_date=date(2026, 5, 1), end_date=date(2026, 7, 31),
                   status=ContractStatus.契約中)
    db.add(up2)
    db.flush()
    low2 = Contract(engineer_id=eng_suzuki.id, project_id=pj_ec.id,
                    contract_type=ContractType.下位, counterparty_client_id=bp_g.id,
                    parent_contract_id=up2.id,
                    unit_price=600_000, settlement_lower=140, settlement_upper=180,
                    overtime_rate=3_750, deduction_rate=3_750,
                    start_date=date(2026, 5, 1), end_date=date(2026, 7, 31),
                    status=ContractStatus.契約中)

    # ペア3: 佐々木 → エンド(上位、自社要員なので下位なし＝直請け)
    up3 = Contract(engineer_id=eng_sasaki.id, project_id=pj_bank.id,
                   contract_type=ContractType.上位, counterparty_client_id=end1.id,
                   unit_price=720_000, settlement_lower=150, settlement_upper=190,
                   overtime_rate=4_500, deduction_rate=4_500,
                   start_date=date(2026, 4, 1), end_date=date(2026, 12, 31),
                   status=ContractStatus.契約中, auto_renew=True)

    # ペア4: 伊藤 → SIer(上位) / BPベータ(下位)、まもなく終了（更新リマインド対象）
    month_end = _add_months(date.today(), 1) - timedelta(days=1)
    up4 = Contract(engineer_id=eng_ito.id,
                   contract_type=ContractType.上位, counterparty_client_id=sier.id,
                   unit_price=640_000, settlement_lower=140, settlement_upper=180,
                   overtime_rate=4_000, deduction_rate=4_000,
                   start_date=date(2026, 1, 1), end_date=month_end,
                   status=ContractStatus.契約中)
    db.add(up4)
    db.flush()
    low4 = Contract(engineer_id=eng_ito.id,
                    contract_type=ContractType.下位, counterparty_client_id=bp_b.id,
                    parent_contract_id=up4.id,
                    unit_price=560_000, settlement_lower=140, settlement_upper=180,
                    overtime_rate=3_500, deduction_rate=3_500,
                    start_date=date(2026, 1, 1), end_date=month_end,
                    status=ContractStatus.契約中)

    db.add_all([low1, low2, up3, low4])
    db.flush()

    # ---- 稼働実績（直近3ヶ月、いろいろな稼働パターン）----
    this_month = date.today().replace(day=1)
    months = [_add_months(this_month, -2), _add_months(this_month, -1), this_month]
    # (契約, [3ヶ月分の稼働時間])  範囲内/超過/不足を織り交ぜる
    work_plan = [
        (up1, [160, 190, 170]), (low1, [160, 190, 170]),  # 2ヶ月目は超過
        (up2, [150, 130, 165]), (low2, [150, 130, 165]),  # 2ヶ月目は不足
        (up3, [170, 175, 180]),
        (up4, [160, 160, 160]), (low4, [160, 160, 160]),
    ]
    for contract, hours_list in work_plan:
        for ym, h in zip(months, hours_list, strict=True):
            db.add(WorkRecord(contract_id=contract.id, year_month=ym, worked_hours=h))
    db.flush()

    # ---- 請求（過去2ヶ月分は確定、当月は未請求）----
    from app.crud.invoice import generate_invoices_for_month

    for ym in months:
        generate_invoices_for_month(db, ym)
    # 過去分のステータスを進める
    past_invoices = db.execute(
        select(Invoice).where(Invoice.year_month < this_month)
    ).scalars().all()
    for inv in past_invoices:
        inv.status = InvoiceStatus.入金済 if inv.year_month == months[0] else InvoiceStatus.請求済
        inv.issued_date = _add_months(inv.year_month, 1)
    db.commit()

    # ---- 社員（自社雇用、外国籍想定で個人情報サブテーブルも）----
    emp = Employee(
        name="張 偉", name_romaji="ZHANG WEI", name_kana="チョウ イ",
        birth_date=date(1993, 9, 23), gender=GenderType.男, nationality="中国",
        mobile_phone="080-5388-0000", email="zhang@example.com",
        postal_code="116-0001", address="東京都荒川区町屋1-1-1 サンプルマンション101",
        hire_date=date(2024, 4, 1), status=EmployeeStatus.在籍,
    )
    db.add(emp)
    db.flush()
    db.add_all([
        EmployeeResidenceCard(employee_id=emp.id, residence_status="技術・人文知識・国際業務",
                              card_number="TR5851234DF", period_text="3年",
                              expiry_date=date(2027, 3, 31), is_current=True),
        EmployeeBankAccount(employee_id=emp.id, bank_name="みずほ銀行", branch_name="町屋支店",
                            branch_code="123", account_number="1234567",
                            account_holder_kana="チョウ イ", is_primary=True),
        EmployeeEmergencyContact(employee_id=emp.id, kind=EmergencyContactKind.在日緊急連絡,
                                 contact_name="李 娜", relationship="配偶者",
                                 phone="080-1111-2222"),
        EmployeeEmergencyContact(employee_id=emp.id, kind=EmergencyContactKind.母国親族,
                                 contact_name="張 国強", relationship="父",
                                 phone="+86-138-0000-0000"),
    ])
    db.commit()
    print(
        "[seed] rich demo data created "
        "(users/clients/engineers/projects/contracts/work/invoices/employee)"
    )


def main() -> None:
    db = SessionLocal()
    try:
        admin = seed_admin(db)
        if os.environ.get("SEED_DEMO") == "1":
            users = seed_users(db, admin)
            seed_demo(db, users)
    finally:
        db.close()


if __name__ == "__main__":
    main()
