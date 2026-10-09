from exceptions.exceptions import station_forbidden_exception
from models.station import StationModel
from models.user import UserModel


def check_station_ownership(
        station: StationModel,
        current_user: UserModel,
) -> None:
    """Ensure that the current user owns the station."""
    if station.user_id != current_user.id:
        raise station_forbidden_exception()
