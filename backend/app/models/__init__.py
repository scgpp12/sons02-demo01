"""モデルの集約。Alembic env.py や seed から `import app.models` で全テーブルを読み込む。"""
from app.db.base import Base
from app.models.client import Client
from app.models.contract import Contract
from app.models.employee import (
    Employee,
    EmployeeBankAccount,
    EmployeeDocument,
    EmployeeEmergencyContact,
    EmployeeEmploymentHistory,
    EmployeeMyNumber,
    EmployeeResidenceCard,
)
from app.models.engineer import Engineer
from app.models.invoice import Invoice
from app.models.project import Project
from app.models.user import User
from app.models.work_record import WorkRecord

__all__ = [
    "Base",
    "User",
    "Engineer",
    "Client",
    "Project",
    "Contract",
    "WorkRecord",
    "Invoice",
    "Employee",
    "EmployeeResidenceCard",
    "EmployeeBankAccount",
    "EmployeeEmergencyContact",
    "EmployeeMyNumber",
    "EmployeeEmploymentHistory",
    "EmployeeDocument",
]
