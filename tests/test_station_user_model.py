"""Unit tests for StationUserModel (station <-> user role assignment)."""
from models.station import StationModel
from models.station_role import StationRoleModel
from models.station_user import StationUserModel
from models.user import UserModel


def _make_station_and_user(db_session):
    user = UserModel.create_user(
        email="station-user@example.com",
        password="StrongPass1!",
        first_name="Owner",
        second_name=None,
        last_name="User",
        session=db_session,
    )
    station = StationModel.create_station(
        session=db_session,
        user_id=user.id,
        name="Staffed STO",
        address="Staffed St",
    )
    db_session.commit()
    return station, user


def test_assign_user_to_station_default_role(db_session):
    station, user = _make_station_and_user(db_session)

    assignment = StationUserModel(station_id=station.id, user_id=user.id)
    db_session.add(assignment)
    db_session.commit()

    assert assignment.id is not None
    assert assignment.role_id == 1  # server_default


def test_assign_user_to_station_with_explicit_role(db_session):
    station, user = _make_station_and_user(db_session)
    role = StationRoleModel(name="Manager", description="Station manager")
    db_session.add(role)
    db_session.flush()

    assignment = StationUserModel(
        station_id=station.id, user_id=user.id, role_id=role.id
    )
    db_session.add(assignment)
    db_session.commit()

    assert assignment.role_id == role.id


def test_duplicate_station_user_assignment_violates_unique_constraint(db_session):
    station, user = _make_station_and_user(db_session)

    db_session.add(StationUserModel(station_id=station.id, user_id=user.id))
    db_session.commit()

    db_session.add(StationUserModel(station_id=station.id, user_id=user.id))

    import pytest
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        db_session.commit()
