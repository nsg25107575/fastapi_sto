import pytest
from fastapi import HTTPException

from auth.authorization import check_station_permission
from models.station import StationModel
from models.station_role import StationRoleModel
from models.station_user import StationUserModel


def _make_station(db_session, owner, name="Test STO"):
    """Create a station owned by the specified user."""
    station = StationModel.create_station(
        session=db_session,
        user_id=owner.id,
        name=name,
        address=f"{name} Address",
    )
    db_session.commit()
    return station


def _assign_role(db_session, station, user, role_name):
    """Create a role and assign it to a user at a station."""
    role = StationRoleModel(
        name=role_name,
        description=f"{role_name} role for testing",
    )
    db_session.add(role)
    db_session.flush()

    assignment = StationUserModel(
        station_id=station.id,
        user_id=user.id,
        role_id=role.id,
    )
    db_session.add(assignment)
    db_session.commit()

    return assignment


def test_station_owner_has_permission(
        db_session,
        user_factory,
):
    owner = user_factory(email="owner-auth@example.com")
    station = _make_station(db_session, owner)

    # The owner can perform any station action.
    check_station_permission(
        station=station,
        current_user=owner,
        session=db_session,
        permission="station.delete",
    )


def test_manager_can_update_station(
        db_session,
        user_factory,
):
    owner = user_factory(email="manager-owner@example.com")
    manager = user_factory(email="manager-employee@example.com")
    station = _make_station(db_session, owner)

    _assign_role(db_session, station, manager, "Manager")

    # Manager has the station.update permission.
    check_station_permission(
        station=station,
        current_user=manager,
        session=db_session,
        permission="station.update",
    )


def test_cashier_cannot_update_station(
        db_session,
        user_factory,
):
    owner = user_factory(email="cashier-owner@example.com")
    cashier = user_factory(email="cashier-employee@example.com")
    station = _make_station(db_session, owner)

    _assign_role(db_session, station, cashier, "Cashier")

    with pytest.raises(HTTPException) as exc_info:
        check_station_permission(
            station=station,
            current_user=cashier,
            session=db_session,
            permission="station.update",
        )

    assert exc_info.value.status_code == 403


def test_employee_of_another_station_has_no_access(
        db_session,
        user_factory,
):
    owner_one = user_factory(email="owner-one@example.com")
    owner_two = user_factory(email="owner-two@example.com")
    manager = user_factory(email="other-station-manager@example.com")

    station_one = _make_station(
        db_session,
        owner_one,
        name="First STO",
    )
    station_two = _make_station(
        db_session,
        owner_two,
        name="Second STO",
    )

    # This manager is assigned only to the second station.
    _assign_role(db_session, station_two, manager, "Manager")

    with pytest.raises(HTTPException) as exc_info:
        check_station_permission(
            station=station_one,
            current_user=manager,
            session=db_session,
            permission="station.update",
        )

    assert exc_info.value.status_code == 403


def test_user_without_station_assignment_has_no_access(
        db_session,
        user_factory,
):
    owner = user_factory(email="unassigned-owner@example.com")
    employee = user_factory(email="unassigned-employee@example.com")
    station = _make_station(db_session, owner)

    # The employee has no station_users assignment.
    with pytest.raises(HTTPException) as exc_info:
        check_station_permission(
            station=station,
            current_user=employee,
            session=db_session,
            permission="station.update",
        )

    assert exc_info.value.status_code == 403
