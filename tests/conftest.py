"""
Shared pytest fixtures.

Tests run against an in-memory SQLite database (not the real MariaDB) so
the suite is fast, hermetic, and doesn't require a running database
server. Each test gets a fresh schema and a FastAPI TestClient wired to
use that isolated session via dependency override.

SQLite is sufficient for everything exercised here: SQLAlchemy ORM CRUD,
relationships, and the plain SQL math functions used by
`StationModel.read_nearest_stations` (acos/radians/cos/sin — all
supported natively). MariaDB-only features (the `FULLTEXT` index /
`MATCH ... AGAINST` used by `StationModel.search_stations_by_name`) are
NOT exercised by the SQLite suite — see docs/TESTING.md for how that
method is covered separately.
"""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure the app's own Config doesn't try to reach a real database or
# pick up a developer's local .env while running the test suite.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("COOKIES_SECRET_KEY", "test-cookie-secret")
os.environ.setdefault("COOKIES_SECURE", "")

import models  # noqa: E402  (import after env setup; registers all models' metadata)
from database.engine import Base, get_session  # noqa: E402
from main import app  # noqa: E402

# A single shared in-memory SQLite database for the whole test process.
# StaticPool keeps the same connection alive across sessions (plain
# `sqlite:///:memory:` would otherwise give every new connection a blank
# database).
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine, "connect")
def _enable_foreign_keys(dbapi_connection, _connection_record):
    """SQLite ignores FK constraints by default — enable them so
    integrity errors (used for duplicate-station tests, etc.) behave the
    same way they would against MariaDB."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(scope="function", autouse=True)
def _fresh_schema():
    """Recreate all tables before every test function for full isolation."""
    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def db_session():
    """A raw SQLAlchemy session for tests that talk to models directly."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


def _override_get_session():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """FastAPI TestClient wired to the isolated SQLite test database."""
    app.dependency_overrides[get_session] = _override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# --- Shared factory fixtures -------------------------------------------------

@pytest.fixture
def user_factory(db_session):
    """Create a persisted UserModel; returns the model instance."""
    from models.user import UserModel

    created = []

    def _make(
        email: str | None = None,
        password: str = "StrongPass1!",
        first_name: str = "Test",
        last_name: str = "User",
    ):
        import uuid
        email = email or f"user-{uuid.uuid4().hex[:8]}@example.com"
        user = UserModel.create_user(
            email=email,
            password=password,
            first_name=first_name,
            second_name=None,
            last_name=last_name,
            session=db_session,
        )
        db_session.commit()
        created.append(user)
        return user

    return _make


@pytest.fixture
def auth_client(client):
    """A TestClient already authenticated as a freshly-registered user.

    Returns (client, user_payload) — user_payload is the sign-up response
    body's user info (id, email) for convenience in assertions.
    """
    import uuid

    email = f"auth-{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": email,
        "password": "StrongPass1!",
        "first_name": "Auth",
        "last_name": "User",
    }
    response = client.post("/auth/sign-up", json=payload)
    assert response.status_code == 201, response.text

    user_payload = dict(response.json()["detail"][0])
    user_payload["email"] = email  # not included in the sign-up response body
    return client, user_payload
