from datetime import date

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbDep
from app.crud.dashboard import build_summary
from app.schemas.dashboard import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardSummary)
def get_dashboard(db: DbDep, _: CurrentUser, today: date | None = None) -> DashboardSummary:
    return build_summary(db, today or date.today())
