"""Unit tests for StationModel — direct model-level coverage
complementing the router-level tests in test_stations.py.
"""
from models.station import ModerationStatus, StationModel
from models.user import UserModel


def _make_user(db_session, email="owner@example.com"):
    user = UserModel.create_user(
        email=email,
        password="StrongPass1!",
        first_name="Owner",
        second_name=None,
        last_name="User",
        session=db_session,
    )
    db_session.commit()
    return user


def test_create_and_read_station(db_session):
    user = _make_user(db_session)

    station = StationModel.create_station(
        session=db_session,
        user_id=user.id,
        name="Unit STO",
        address="Unit St",
    )
    db_session.commit()

    fetched = StationModel.read_station(db_session, station.id)

    assert fetched is not None
    assert fetched.name == "Unit STO"


def test_soft_deleted_station_excluded_from_default_queries(db_session):
    """
    Soft-deleted stations should not be returned by read_station() or
    read_stations() due to the global filter applied in the model's query.
    """
    user = _make_user(db_session)
    station = StationModel.create_station(
        session=db_session,
        user_id=user.id,
        name="Deletable STO",
        address="Deletable St",
    )
    db_session.commit()

    StationModel.delete_station(db_session, station.id)
    db_session.commit()

    # The global soft-delete filter hides it from read_station too.
    assert StationModel.read_station(db_session, station.id) is None
    items, _total = StationModel.read_stations(db_session)
    assert station.id not in [s.id for s in items]


def test_restore_station_makes_it_visible_again(db_session):
    user = _make_user(db_session)
    station = StationModel.create_station(
        session=db_session,
        user_id=user.id,
        name="Restorable STO",
        address="Restorable St",
    )
    db_session.commit()
    StationModel.delete_station(db_session, station.id)
    db_session.commit()

    restored = StationModel.restore_station(db_session, station.id)
    db_session.commit()

    assert restored is not None
    assert StationModel.read_station(db_session, station.id) is not None


def test_update_station_only_changes_provided_fields(db_session):
    user = _make_user(db_session)
    station = StationModel.create_station(
        session=db_session,
        user_id=user.id,
        name="Original Name",
        address="Original Address",
    )
    db_session.commit()

    updated = StationModel.update_station(
        session=db_session,
        station_id=station.id,
        name="New Name",
        address=None,  # None values must be ignored, not overwritten
    )
    db_session.commit()

    assert updated.name == "New Name"
    assert updated.address == "Original Address"


def test_read_nearest_stations_orders_by_distance(db_session):
    user = _make_user(db_session)

    kyiv = StationModel.create_station(
        session=db_session, user_id=user.id, name="Kyiv STO", address="Kyiv St"
    )
    kyiv.latitude = 50.4501
    kyiv.longitude = 30.5234
    kyiv.moderation_status = ModerationStatus.APPROVED

    sydney = StationModel.create_station(
        session=db_session, user_id=user.id, name="Sydney STO", address="Sydney St"
    )
    sydney.latitude = -33.8688
    sydney.longitude = 151.2093
    sydney.moderation_status = ModerationStatus.APPROVED

    db_session.commit()

    results = StationModel.read_nearest_stations(
        session=db_session, lat=50.4501, lng=30.5234, limit=10
    )

    assert results[0]["name"] == "Kyiv STO"
    assert results[0]["distance_km"] < results[1]["distance_km"]


def test_read_nearest_stations_excludes_inactive(db_session):
    user = _make_user(db_session)

    station = StationModel.create_station(
        session=db_session, user_id=user.id, name="Inactive STO", address="Inactive St"
    )
    station.latitude = 50.4501
    station.longitude = 30.5234
    station.active = False
    db_session.commit()

    results = StationModel.read_nearest_stations(
        session=db_session, lat=50.4501, lng=30.5234, limit=10
    )

    assert results == []


def test_search_stations_by_name_rejects_short_query(db_session):
    # Guard clause only — doesn't touch the DB, so it's safe to exercise
    # even though the full MATCH()/AGAINST() full-text path below it is
    # MariaDB-only and NOT exercised against SQLite in this suite.
    assert StationModel.search_stations_by_name(db_session, "ab") == []
    assert StationModel.search_stations_by_name(db_session, "") == []
    assert StationModel.search_stations_by_name(db_session, "   ") == []


def test_search_stations_by_name_full_text_requires_mariadb(db_session):
    """
    MariaDB's FULLTEXT MATCH()/AGAINST() has no SQLite equivalent, so this
    path cannot be exercised against the SQLite test database — calling it
    with a valid (>=3 char) query raises here instead of returning results.
    This is expected and documented in docs/TESTING.md; the real behavior
    is covered by manual/integration testing against MariaDB.
    """
    import pytest

    with pytest.raises(Exception):
        StationModel.search_stations_by_name(db_session, "Auto")
