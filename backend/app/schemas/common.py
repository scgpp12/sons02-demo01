"""共通スキーマ（ページング等）。"""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """一覧APIの共通レスポンス。"""

    items: list[T]
    total: int
    page: int
    page_size: int


class Msg(BaseModel):
    detail: str
