"""モデル共通のカラム型ヘルパ。"""
import enum
from typing import Any

from sqlalchemy import Enum as SAEnum


def pg_enum(py_enum: type[enum.Enum], name: str) -> SAEnum:
    """既存のPostgreSQL ENUM型(マイグレーションで作成済み)にマップする。

    - native_enum=True : ネイティブENUMを使う
    - create_type=False: 型生成はAlembic生DDL側が責務（二重生成を防ぐ）
    - values_callable  : メンバ名でなく .value(日本語等)を保存
    """
    return SAEnum(
        py_enum,
        name=name,
        native_enum=True,
        create_type=False,
        values_callable=lambda e: [m.value for m in e],
    )


# JSONBデフォルト用
EMPTY_LIST: Any = list
