"""Unit tests for StationServiceModel (price list CRUD + aggregation)."""
from models.station import StationModel
from models.station_service import StationServiceModel
from models.user import UserModel


def _make_station(db_session):
    user = UserModel.create_user(
        email="svc-owner@example.com",
        password="StrongPass1!",
        first_name="Owner",
        second_name=None,
        last_name="User",
        session=db_session,
    )
    station = StationModel.create_station(
        session=db_session,
        user_id=user.id,
        name="Service Model STO",
        address="Service Model St",
    )
    db_session.commit()
    return station


def test_add_service(db_session):
    station = _make_station(db_session)

    service = StationServiceModel.add_service(
        session=db_session, station_id=station.id, name="Oil change", price=25.0
    )

    assert service.id is not None
    assert service.price == 25.0


def test_update_service_partial_fields(db_session):
    station = _make_station(db_session)
    service = StationServiceModel.add_service(
        session=db_session, station_id=station.id, name="Tire change", price=10.0
    )

    updated = StationServiceModel.update_service(
        session=db_session, service_id=service.id, price=15.0
    )

    assert updated.name == "Tire change"  # unchanged
    assert updated.price == 15.0


def test_update_service_not_found_returns_none(db_session):
    result = StationServiceModel.update_service(
        session=db_session, service_id=999999, price=1.0
    )

    assert result is None


def test_delete_service(db_session):
    station = _make_station(db_session)
    service = StationServiceModel.add_service(
        session=db_session, station_id=station.id, name="Wash", price=3.0
    )

    deleted_id = StationServiceModel.delete_service(
        session=db_session, service_id=service.id
    )

    assert deleted_id == service.id
    assert StationServiceModel.get_service(db_session, service.id) is None


def test_get_services_returns_distinct_names(db_session):
    """
    Test that get_services returns distinct service names,
    even if multiple price rows exist for the same service.
    """
    station = _make_station(db_session)
    StationServiceModel.add_service(
        session=db_session, station_id=station.id, name="Brake check", price=20.0
    )
    StationServiceModel.add_service(
        session=db_session, station_id=station.id, name="Brake check", price=35.0
    )
    StationServiceModel.add_service(
        session=db_session, station_id=station.id, name="Oil change", price=10.0
    )

    items, total = StationServiceModel.get_services(db_session)

    assert total == 2  # "Brake check" counted once
    assert sorted(items) == ["Brake check", "Oil change"]
