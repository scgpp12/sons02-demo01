from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.core.deps import CurrentUser, DbDep, ensure_can_edit
from app.crud.base import CRUDBase
from app.models.client import Client
from app.models.enums import ProjectStatus
from app.models.project import Project
from app.schemas.common import Page
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])
crud = CRUDBase(Project)


def _to_read(project: Project, client_name: str | None) -> ProjectRead:
    out = ProjectRead.model_validate(project)
    out.client_name = client_name
    return out


@router.get("", response_model=Page[ProjectRead])
def list_projects(
    db: DbDep,
    _: CurrentUser,
    q: str | None = Query(None, description="案件名の部分一致"),
    status_: ProjectStatus | None = Query(None, alias="status"),
    client_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Page[ProjectRead]:
    stmt = select(Project, Client.company_name).outerjoin(Client, Client.id == Project.client_id)
    if q:
        stmt = stmt.where(Project.title.ilike(f"%{q}%"))
    if status_:
        stmt = stmt.where(Project.status == status_)
    if client_id:
        stmt = stmt.where(Project.client_id == client_id)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    stmt = stmt.order_by(Project.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = db.execute(stmt).all()
    items = [_to_read(p, cname) for p, cname in rows]
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: DbDep, _: CurrentUser) -> ProjectRead:
    obj = crud.get(db, project_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "案件が見つかりません")
    client = db.get(Client, obj.client_id)
    return _to_read(obj, client.company_name if client else None)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: DbDep, user: CurrentUser) -> ProjectRead:
    # model_dump()はネストしたSkillもdictに直列化する
    data = payload.model_dump()
    data["created_by"] = user.id
    obj = crud.create(db, data)
    client = db.get(Client, obj.client_id)
    return _to_read(obj, client.company_name if client else None)


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int, payload: ProjectUpdate, db: DbDep, user: CurrentUser
) -> ProjectRead:
    obj = crud.get(db, project_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "案件が見つかりません")
    ensure_can_edit(user, obj.created_by)
    data = payload.model_dump(exclude_unset=True)
    obj = crud.update(db, obj, data)
    client = db.get(Client, obj.client_id)
    return _to_read(obj, client.company_name if client else None)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: DbDep, user: CurrentUser) -> None:
    obj = crud.get(db, project_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "案件が見つかりません")
    ensure_can_edit(user, obj.created_by)
    crud.delete(db, obj)
