from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import ProjectStatus
from app.schemas.engineer import Skill


class ProjectBase(BaseModel):
    client_id: int
    title: str
    required_skills: list[Skill] = []
    unit_price_min: int | None = None
    unit_price_max: int | None = None
    headcount: int = 1
    work_location: str | None = None
    remote_ok: bool = False
    start_date: date | None = None
    status: ProjectStatus = ProjectStatus.募集中
    note: str | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    client_id: int | None = None
    title: str | None = None
    required_skills: list[Skill] | None = None
    unit_price_min: int | None = None
    unit_price_max: int | None = None
    headcount: int | None = None
    work_location: str | None = None
    remote_ok: bool | None = None
    start_date: date | None = None
    status: ProjectStatus | None = None
    note: str | None = None


class ProjectRead(ProjectBase):
    id: int
    client_name: str | None = None
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
