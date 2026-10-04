"""Unit tests for the generic database.pagination.paginate() helper."""

from sqlalchemy import select

from database.pagination import paginate
from models.user import UserModel


def test_paginate_returns_items_and_total(db_session):
    """
    Test that the paginate function returns the correct number of items and total count.
    """
    for i in range(5):
        UserModel.create_user(
            email=f"user{i}@example.com",
            password="secret",
            first_name="Test",
            second_name=None,
            last_name="User",
            session=db_session,
        )
    db_session.commit()

    items, total = paginate(db_session, select(UserModel), offset=0, limit=2)

    assert total == 5
    assert len(items) == 2


def test_paginate_total_unaffected_by_offset_limit(db_session):
    """
    Test that the total count returned by paginate is unaffected by offset and limit.
    """
    for i in range(5):
        UserModel.create_user(
            email=f"user{i}@example.com",
            password="secret",
            first_name="Test",
            second_name=None,
            last_name="User",
            session=db_session,
        )
    db_session.commit()

    items, total = paginate(db_session, select(UserModel), offset=4, limit=2)

    assert total == 5
    assert len(items) == 1  # only 1 row left after offset 4


def test_paginate_empty_table(db_session):
    """
    Test that paginate returns an empty list and total count of 0 for an empty table.
    """
    items, total = paginate(db_session, select(UserModel), offset=0, limit=20)

    assert items == []
    assert total == 0
