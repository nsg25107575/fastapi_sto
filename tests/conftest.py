import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from routers.stations import get_session

TEST_DATABASE_URL = (
    "mariadb+mariadbconnector://"
    "stations_user:stations_password"
    "@localhost/stations_test_db"
)

test_engine = create_engine(
    TEST_DATABASE_URL
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False
)


def get_test_session():
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    app.dependency_overrides[get_session] = get_test_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
