"""汎用CRUD操作。単純なマスタはこれで賄い、結合や特殊フィルタは各routerで補う。"""
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class CRUDBase(Generic[ModelT]):
    def __init__(self, model: type[ModelT]):
        self.model = model

    def get(self, db: Session, id: int) -> ModelT | None:
        return db.get(self.model, id)

    def create(self, db: Session, data: dict[str, Any]) -> ModelT:
        obj = self.model(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, obj: ModelT, data: dict[str, Any]) -> ModelT:
        for k, v in data.items():
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, obj: ModelT) -> None:
        db.delete(obj)
        db.commit()

    def count(self, db: Session, *conditions: Any) -> int:
        stmt = select(func.count()).select_from(self.model)
        for c in conditions:
            stmt = stmt.where(c)
        return db.execute(stmt).scalar_one()
