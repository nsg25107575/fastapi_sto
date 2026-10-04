from typing import Any, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

T = TypeVar("T")


def paginate(session: Session, stmt: Select[Any], offset: int, limit: int) -> tuple[list[T], int]:
    """
    Apply offset/limit pagination to any SQLAlchemy select statement.
    Returns (items, total_count).
    """
    total = session.scalar(
        select(func.count()).select_from(stmt.subquery())
    ) or 0

    items = session.scalars(
        stmt.offset(offset).limit(limit)
    ).all()

    return list(items), total
