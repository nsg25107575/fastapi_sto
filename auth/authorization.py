from sqlalchemy import select
from sqlalchemy.orm import Session

from exceptions.exceptions import (
    admin_forbidden_exception,
    station_forbidden_exception,
)
from models.station import StationModel
from models.station_role import StationRoleModel
from models.station_user import StationUserModel
from models.user import UserModel

# Permissions assigned to station employees.
# Keep this policy explicit: a role receives only listed permissions.
ROLE_PERMISSIONS = {
    "Manager": {
        "station.update",
        "service.manage",
        "station_contact.manage",
        "order.manage",
    },
    "Cashier": set(),
    "Fuel Attendant": set(),
    "Maintenance Staff": set(),
    "Security Personnel": set(),
}


def check_station_ownership(
        station: StationModel,
        current_user: UserModel,
) -> None:
    """Ensure that the current user owns the station."""
    if station.user_id != current_user.id:
        raise station_forbidden_exception()


def check_admin_access(current_user: UserModel) -> None:
    """Ensure that the current user has administrator privileges."""
    if not current_user.is_admin:
        raise admin_forbidden_exception()


def check_station_permission(
        station: StationModel,
        current_user: UserModel,
        session: Session,
        permission: str = "station.update",
) -> None:
    """Check whether the user can perform an action on this station.

    The station owner has full access.
    Other users must have a station_users assignment and a role
    explicitly granting the requested permission.
    """
    # The station owner has full access to their own station.
    if station.user_id == current_user.id:
        return

    # Find this user's role for this specific station.
    stmt = (
        select(StationRoleModel.name)
        .join(
            StationUserModel,
            StationUserModel.role_id == StationRoleModel.id,
        )
        .where(
            StationUserModel.station_id == station.id,
            StationUserModel.user_id == current_user.id,
        )
    )

    role_name = session.scalar(stmt)

    # No assignment, unknown role, or missing permission means no access.
    if permission not in ROLE_PERMISSIONS.get(role_name, set()):
        raise station_forbidden_exception()
