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

# Keep locale-dependent API tests deterministic in environments whose .env
# does not configure all application locales (such as the CI image).
os.environ["APP_DEFAULT_LOCALE"] = "en"
os.environ["APP_SUPPORTED_LOCALES"] = (
    '[{"abbr":"en","name":"English"},'
    '{"abbr":"uk","name":"Українська"},'
    '{"abbr":"pl","name":"Polski"}]'
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Force (not setdefault!) these so the suite is identical whether run on
# a bare host or inside the `api` container — where docker-compose.yml
# already injects a real DATABASE_URL/COOKIES_SECURE/etc. as OS-level env
# vars before Python even starts. `setdefault` would silently keep those
# container values (e.g. COOKIES_SECURE=True), which breaks the `station`
# cookie round-trip against TestClient's plain-http requests and makes
# every authenticated test fail with 401 — see docs/ISSUES.md.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-at-least-32-bytes-long"
# auth/config.py's LoginManager is actually keyed off COOKIES_SECRET_KEY
# (Config.cookie_secret), not JWT_SECRET_KEY — PyJWT/fastapi-login emit
# InsecureKeyLengthWarning for any HMAC key under 32 bytes, so this must
# be >= 32 chars too, not just "long enough to look like a secret".
os.environ["COOKIES_SECRET_KEY"] = "test-cookie-secret-at-least-32-bytes-long"
os.environ["COOKIES_SECURE"] = ""

import database.engine as db_engine_module  # noqa: E402

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

# IMPORTANT: some routers (e.g. routers/auth.py) open sessions directly via
# `with Session(engine) as session:` using the module-level `engine` from
# database.engine, instead of the `get_session` FastAPI dependency. That
# bypasses `app.dependency_overrides`, so those routes would otherwise hit
# the real configured database. Patch the shared module objects BEFORE
# importing `main` (which imports all routers) so every `from
# database.engine import engine` picks up the test engine transitively.
# See docs/ISSUES.md (ISSUE-18) for the underlying design fix.
db_engine_module.engine = test_engine
db_engine_module.SessionLocal = TestSessionLocal

from database.engine import Base, get_session  # noqa: E402
from main import app  # noqa: E402


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


@pytest.fixture(autouse=True)
def _stub_geocoding(monkeypatch):
    """Autouse so no test needs to opt in explicitly: `POST /stations`
    now geocodes the address (see routers/stations.py), and the suite
    must never make a real network call to the Nominatim API. Returns a
    fixed Kyiv coordinate for any address; tests that need a specific
    other geocoding behavior (success/failure) override this directly,
    see tests/test_geocoding.py."""
    monkeypatch.setattr(
        "routers.stations.geocode_address",
        lambda address: (50.4501, 30.5234),
    )


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


@pytest.fixture
def second_auth_client(client):
    """A second authenticated client sharing the test database."""
    import uuid

    second_client = TestClient(app)

    email = f"second-{uuid.uuid4().hex[:8]}@example.com"
    response = second_client.post(
        "/auth/sign-up",
        json={
            "email": email,
            "password": "StrongPass1!",
            "first_name": "Second",
            "last_name": "User",
        },
    )
    assert response.status_code == 201, response.text

    yield second_client
    second_client.close()
