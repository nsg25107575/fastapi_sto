"""Unit tests for UserModel (lookup/creation helpers)."""
from datetime import datetime, timezone

from auth.dependencies import load_user
from models.token import TokenModel
from models.user import UserModel


def test_create_user_persists_record(db_session):
    user = UserModel.create_user(
        email="lookup@example.com",
        password="StrongPass1!",
        first_name="Lookup",
        second_name=None,
        last_name="User",
        session=db_session,
    )
    db_session.commit()

    assert user.id is not None


def test_get_user_by_email_found(db_session):
    UserModel.create_user(
        email="findme@example.com",
        password="StrongPass1!",
        first_name="Find",
        second_name=None,
        last_name="Me",
        session=db_session,
    )
    db_session.commit()

    found = UserModel.get_user_by_email("findme@example.com", db_session)

    assert found is not None
    assert found.email == "findme@example.com"


def test_get_user_by_email_not_found_returns_none(db_session):
    result = UserModel.get_user_by_email("nobody@example.com", db_session)

    assert result is None


def test_get_user_by_email_excludes_soft_deleted_user(db_session):
    user = UserModel.create_user(
        email="deleted@example.com",
        password="StrongPass1!",
        first_name="Deleted",
        second_name=None,
        last_name="User",
        session=db_session,
    )
    db_session.commit()

    user.deleted_at = datetime.now()
    db_session.commit()

    found = UserModel.get_user_by_email("deleted@example.com", db_session)

    assert found is None


def test_load_user_excludes_soft_deleted_user(db_session):
    user = UserModel.create_user(
        email="deleted-auth@example.com",
        password="StrongPass1!",
        first_name="Deleted",
        second_name=None,
        last_name="User",
        session=db_session,
    )

    TokenModel.save_token(
        user_id=user.id,
        access_token="test-token",
        session=db_session,
    )

    user.deleted_at = datetime.now(timezone.utc)
    db_session.commit()

    loaded_user = load_user(user.email)

    assert loaded_user is None
