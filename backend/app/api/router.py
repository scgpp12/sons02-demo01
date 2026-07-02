"""全routerの集約。"""
from fastapi import APIRouter

from app.api import (
    auth,
    clients,
    contracts,
    dashboard,
    employees,
    engineers,
    invoices,
    projects,
    users,
    work_records,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(engineers.router)
api_router.include_router(clients.router)
api_router.include_router(projects.router)
api_router.include_router(contracts.router)
api_router.include_router(work_records.router)
api_router.include_router(invoices.router)
api_router.include_router(employees.router)
api_router.include_router(dashboard.router)
api_router.include_router(users.router)
