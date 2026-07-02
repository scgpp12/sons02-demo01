"""結合テスト用の共通フィクスチャ。

- 実PostgreSQL（テスト用DB）に対して alembic でスキーマを構築
- 各テスト前に全テーブルを TRUNCATE して admin を再投入（テスト間独立）
- httpx ベースの TestClient + 認証ヘッダを払い出す

テスト用DBは環境変数 TEST_DATABASE_URL で指定（既定: localhost:55432/ses_test）。
Windowsローカルでは PYTHONUTF8=1 を付けて実行すること。
"""
import os

# app をimportする前にDB接続先を確定させる
TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://ses:ses_pass@localhost:55432/ses_test"
)
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("ADMIN_PASSWORD", "admin123")

import pytest  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from alembic import command  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.models.user import User  # noqa: E402

ALL_TABLES = [
    "employee_documents",
    "employee_employment_history",
    "employee_my_number",
    "employee_emergency_contacts",
    "employee_bank_accounts",
    "employee_residence_cards",
    "employees",
    "invoices",
    "work_records",
    "contracts",
    "projects",
    "clients",
    "engineers",
    "users",
]


def _db_reachable() -> bool:
    try:
        with engine.connect():
            return True
    except Exception:
        return False


@pytest.fixture(scope="session", autouse=True)
def _schema():
    """セッション開始時にスキーマを作り直す。DB未起動ならスキップ。"""
    if not _db_reachable():
        pytest.skip(
            f"テスト用PostgreSQLに接続できません（{TEST_DB_URL}）。"
            "docker等でDBを起動してから実行してください。",
            allow_module_level=True,
        )
    cfg = Config("alembic.ini")
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def _clean_db():
    """各テスト前にデータを全消去し、admin を1人だけ投入。"""
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {', '.join(ALL_TABLES)} RESTART IDENTITY CASCADE"))
    db = SessionLocal()
    db.add(
        User(
            email="admin@example.com",
            name="管理者",
            role=UserRole.admin,
            is_active=True,
            password_hash=hash_password("admin123"),
        )
    )
    db.commit()
    db.close()
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _login(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/auth/login", data={"username": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def admin_headers(client: TestClient) -> dict[str, str]:
    token = _login(client, "admin@example.com", "admin123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def make_user(client: TestClient, admin_headers):
    """admin権限で任意ロールのユーザーを作り、その認証ヘッダを返すファクトリ。"""

    def _make(email: str, role: str, password: str = "pass1234"):
        res = client.post(
            "/api/users",
            headers=admin_headers,
            json={"email": email, "name": email, "role": role, "password": password},
        )
        assert res.status_code == 201, res.text
        token = _login(client, email, password)
        return {"Authorization": f"Bearer {token}"}

    return _make
