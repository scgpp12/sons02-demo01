"""initial schema (ses + employee)

Revision ID: 0001
Revises:
Create Date: 2026-06-18
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# 提供されたDDL(ses_schema.sql + employee_schema.sql)をそのまま初期マイグレーションに採用。
# ENUM・トリガ関数・GINインデックスを含む。seed(admin)はseed.pyが担当するため除外。
UPGRADE_SQL = r"""
-- ENUM型
CREATE TYPE user_role        AS ENUM ('admin', 'manager', 'sales');
CREATE TYPE engineer_status  AS ENUM ('待機', '稼働中', '契約終了予定', '離脱');
CREATE TYPE business_type    AS ENUM ('エンド', 'SIer', 'コンサル', 'BP');
CREATE TYPE project_status   AS ENUM ('募集中', '提案中', '成約', 'クローズ');
CREATE TYPE contract_type    AS ENUM ('上位', '下位');
CREATE TYPE contract_status  AS ENUM ('契約中', '更新待ち', '終了');
CREATE TYPE invoice_status   AS ENUM ('未請求', '請求済', '入金済');
CREATE TYPE gender_type            AS ENUM ('男', '女', 'その他', '未回答');
CREATE TYPE employee_status        AS ENUM ('在籍', '休職', '退職');
CREATE TYPE emergency_contact_kind AS ENUM ('母国親族', '在日緊急連絡', 'その他');
CREATE TYPE document_kind          AS ENUM (
  '在留カード表', '在留カード裏', 'パスポート', '証明写真',
  '源泉徴収票', 'マイナンバーカード', 'その他');

-- updated_at 自動更新トリガ関数（共通）
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- users
CREATE TABLE users (
  id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email          VARCHAR(255) NOT NULL UNIQUE,
  password_hash  VARCHAR(255) NOT NULL,
  name           VARCHAR(100) NOT NULL,
  role           user_role    NOT NULL DEFAULT 'sales',
  is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_users_updated BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- engineers
CREATE TABLE engineers (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name            VARCHAR(100) NOT NULL,
  name_kana       VARCHAR(100),
  email           VARCHAR(255),
  phone           VARCHAR(30),
  skills          JSONB        NOT NULL DEFAULT '[]',
  skill_sheet_path VARCHAR(500),
  unit_price      INTEGER,
  status          engineer_status NOT NULL DEFAULT '待機',
  available_from  DATE,
  remote_ok       BOOLEAN      NOT NULL DEFAULT FALSE,
  note            TEXT,
  created_by      BIGINT REFERENCES users(id),
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_engineers_status ON engineers(status);
CREATE INDEX idx_engineers_skills ON engineers USING GIN (skills);
CREATE TRIGGER trg_engineers_updated BEFORE UPDATE ON engineers
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- clients
CREATE TABLE clients (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  company_name    VARCHAR(200) NOT NULL,
  business_type   business_type NOT NULL,
  contact_name    VARCHAR(100),
  contact_email   VARCHAR(255),
  contact_phone   VARCHAR(30),
  can_distribute  BOOLEAN      NOT NULL DEFAULT TRUE,
  note            TEXT,
  created_by      BIGINT REFERENCES users(id),
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_clients_business_type ON clients(business_type);
CREATE TRIGGER trg_clients_updated BEFORE UPDATE ON clients
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- projects
CREATE TABLE projects (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  client_id       BIGINT NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
  title           VARCHAR(200) NOT NULL,
  required_skills JSONB        NOT NULL DEFAULT '[]',
  unit_price_min  INTEGER,
  unit_price_max  INTEGER,
  headcount       INTEGER      NOT NULL DEFAULT 1,
  work_location   VARCHAR(200),
  remote_ok       BOOLEAN      NOT NULL DEFAULT FALSE,
  start_date      DATE,
  status          project_status NOT NULL DEFAULT '募集中',
  note            TEXT,
  created_by      BIGINT REFERENCES users(id),
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_client ON projects(client_id);
CREATE TRIGGER trg_projects_updated BEFORE UPDATE ON projects
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- contracts
CREATE TABLE contracts (
  id                    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  engineer_id           BIGINT NOT NULL REFERENCES engineers(id) ON DELETE RESTRICT,
  project_id            BIGINT REFERENCES projects(id) ON DELETE SET NULL,
  contract_type         contract_type NOT NULL,
  counterparty_client_id BIGINT REFERENCES clients(id) ON DELETE RESTRICT,
  parent_contract_id    BIGINT REFERENCES contracts(id) ON DELETE SET NULL,
  unit_price            INTEGER NOT NULL,
  settlement_lower      INTEGER,
  settlement_upper      INTEGER,
  overtime_rate         INTEGER DEFAULT 0,
  deduction_rate        INTEGER DEFAULT 0,
  start_date            DATE NOT NULL,
  end_date              DATE NOT NULL,
  auto_renew            BOOLEAN NOT NULL DEFAULT FALSE,
  status                contract_status NOT NULL DEFAULT '契約中',
  contract_file_path    VARCHAR(500),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_settlement CHECK (
    settlement_lower IS NULL OR settlement_upper IS NULL
    OR settlement_lower <= settlement_upper
  )
);
CREATE INDEX idx_contracts_engineer ON contracts(engineer_id);
CREATE INDEX idx_contracts_status   ON contracts(status);
CREATE INDEX idx_contracts_enddate  ON contracts(end_date);
CREATE INDEX idx_contracts_parent   ON contracts(parent_contract_id);
CREATE TRIGGER trg_contracts_updated BEFORE UPDATE ON contracts
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- work_records
CREATE TABLE work_records (
  id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  contract_id   BIGINT NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
  year_month    DATE   NOT NULL,
  worked_hours  NUMERIC(6,2) NOT NULL DEFAULT 0,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_work_contract_month UNIQUE (contract_id, year_month)
);
CREATE INDEX idx_work_records_month ON work_records(year_month);
CREATE TRIGGER trg_work_records_updated BEFORE UPDATE ON work_records
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- invoices
CREATE TABLE invoices (
  id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  contract_id   BIGINT NOT NULL REFERENCES contracts(id) ON DELETE RESTRICT,
  year_month    DATE   NOT NULL,
  billed_amount INTEGER NOT NULL DEFAULT 0,
  status        invoice_status NOT NULL DEFAULT '未請求',
  issued_date   DATE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_invoice_contract_month UNIQUE (contract_id, year_month)
);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_month  ON invoices(year_month);
CREATE TRIGGER trg_invoices_updated BEFORE UPDATE ON invoices
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- employees
CREATE TABLE employees (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id         BIGINT REFERENCES users(id) ON DELETE SET NULL,
  name            VARCHAR(100) NOT NULL,
  name_romaji     VARCHAR(150) NOT NULL,
  name_kana       VARCHAR(150) NOT NULL,
  birth_date      DATE         NOT NULL,
  gender          gender_type,
  nationality     VARCHAR(80)  NOT NULL,
  mobile_phone    VARCHAR(20),
  email           VARCHAR(255),
  postal_code     VARCHAR(8),
  address         VARCHAR(300),
  hire_date       DATE,
  status          employee_status NOT NULL DEFAULT '在籍',
  note            TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_employees_status ON employees(status);
CREATE TRIGGER trg_employees_updated BEFORE UPDATE ON employees
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- employee_residence_cards
CREATE TABLE employee_residence_cards (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  employee_id     BIGINT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
  residence_status VARCHAR(100) NOT NULL,
  card_number     VARCHAR(20)  NOT NULL,
  period_text     VARCHAR(20),
  expiry_date     DATE         NOT NULL,
  is_current      BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_rescard_employee ON employee_residence_cards(employee_id);
CREATE INDEX idx_rescard_expiry   ON employee_residence_cards(expiry_date);
CREATE TRIGGER trg_rescard_updated BEFORE UPDATE ON employee_residence_cards
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- employee_bank_accounts
CREATE TABLE employee_bank_accounts (
  id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  employee_id       BIGINT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
  bank_code         VARCHAR(4),
  bank_name         VARCHAR(100),
  branch_name       VARCHAR(100),
  branch_code       VARCHAR(3),
  account_number    VARCHAR(7),
  account_holder_kana VARCHAR(150),
  is_primary        BOOLEAN NOT NULL DEFAULT TRUE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_bank_employee ON employee_bank_accounts(employee_id);
CREATE TRIGGER trg_bank_updated BEFORE UPDATE ON employee_bank_accounts
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- employee_emergency_contacts
CREATE TABLE employee_emergency_contacts (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  employee_id     BIGINT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
  kind            emergency_contact_kind NOT NULL,
  contact_name    VARCHAR(100) NOT NULL,
  relationship    VARCHAR(50),
  phone           VARCHAR(30)  NOT NULL,
  note            TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_emergency_employee ON employee_emergency_contacts(employee_id);
CREATE TRIGGER trg_emergency_updated BEFORE UPDATE ON employee_emergency_contacts
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- employee_my_number
CREATE TABLE employee_my_number (
  employee_id     BIGINT PRIMARY KEY REFERENCES employees(id) ON DELETE CASCADE,
  my_number_enc   TEXT,
  has_card        BOOLEAN NOT NULL DEFAULT FALSE,
  collected_at    DATE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_mynumber_updated BEFORE UPDATE ON employee_my_number
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- employee_employment_history
CREATE TABLE employee_employment_history (
  id                       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  employee_id              BIGINT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
  employment_insurance_no  VARCHAR(20),
  previous_company_name    VARCHAR(200),
  has_withholding_slip     BOOLEAN NOT NULL DEFAULT FALSE,
  withholding_year         INTEGER,
  note                     TEXT,
  created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_emphist_employee ON employee_employment_history(employee_id);
CREATE TRIGGER trg_emphist_updated BEFORE UPDATE ON employee_employment_history
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- employee_documents
CREATE TABLE employee_documents (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  employee_id     BIGINT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
  doc_kind        document_kind NOT NULL,
  file_path       VARCHAR(500) NOT NULL,
  original_name   VARCHAR(255),
  uploaded_by     BIGINT REFERENCES users(id),
  uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_docs_employee ON employee_documents(employee_id);
CREATE INDEX idx_docs_kind     ON employee_documents(doc_kind);
"""

DOWNGRADE_SQL = r"""
DROP TABLE IF EXISTS employee_documents CASCADE;
DROP TABLE IF EXISTS employee_employment_history CASCADE;
DROP TABLE IF EXISTS employee_my_number CASCADE;
DROP TABLE IF EXISTS employee_emergency_contacts CASCADE;
DROP TABLE IF EXISTS employee_bank_accounts CASCADE;
DROP TABLE IF EXISTS employee_residence_cards CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS invoices CASCADE;
DROP TABLE IF EXISTS work_records CASCADE;
DROP TABLE IF EXISTS contracts CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS clients CASCADE;
DROP TABLE IF EXISTS engineers CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP FUNCTION IF EXISTS set_updated_at() CASCADE;
DROP TYPE IF EXISTS document_kind;
DROP TYPE IF EXISTS emergency_contact_kind;
DROP TYPE IF EXISTS employee_status;
DROP TYPE IF EXISTS gender_type;
DROP TYPE IF EXISTS invoice_status;
DROP TYPE IF EXISTS contract_status;
DROP TYPE IF EXISTS contract_type;
DROP TYPE IF EXISTS project_status;
DROP TYPE IF EXISTS business_type;
DROP TYPE IF EXISTS engineer_status;
DROP TYPE IF EXISTS user_role;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
