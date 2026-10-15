from fastapi import APIRouter, Depends, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth.authorization import check_admin_access, check_station_ownership
from auth.dependencies import get_current_user
from config import Config
from database.engine import get_session
from exceptions import (
    duplicate_station_exception,
    geocoding_failed_exception,
    invalid_coordinate_exception,
    station_not_found_exception,
)
from models.station import ModerationStatus, StationModel
from models.user import UserModel
from services.geocoding import GeocodingError, geocode_address
from validations.pagination import PaginatedResponse, PaginationParams
from validations.station import (
    NearestStationResponseSchema,
    NearestStationsSchema,
    StationCreateSchema,
    StationModerationResponseSchema,
    StationModerationSchema,
    StationResponseSchema,
    StationUpdateSchema,
)

router = APIRouter(
    prefix="/stations",
    tags=["Stations"],
)


@router.post(
    "/",
    response_model=StationResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def add_station(
        payload: StationCreateSchema,
        current_user: UserModel = Depends(get_current_user),
        session: Session = Depends(get_session),
):
    # Resolve the address to coordinates before touching the DB.
    # This prevents creating a station without coordinates if geocoding fails.
    try:
        latitude, longitude = geocode_address(payload.address)
    except GeocodingError:
        raise geocoding_failed_exception()

    try:
        station = StationModel.create_station(
            session=session,
            user_id=current_user.id,
            name=payload.name,
            address=payload.address,
        )

        station.latitude = latitude
        station.longitude = longitude

        session.commit()
        session.refresh(station)

        return station

    except IntegrityError:
        session.rollback()
        raise duplicate_station_exception()


@router.get(
    "/",
    response_model=PaginatedResponse[StationResponseSchema],
    status_code=status.HTTP_200_OK,
)
def get_stations(
        pagination: PaginationParams = Depends(),
        session: Session = Depends(get_session),
):
    items, total = StationModel.read_stations(
        session,
        pagination.offset,
        pagination.limit,
    )

    return PaginatedResponse(
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get(
    "/nearest",
    response_model=list[NearestStationResponseSchema],
)
def get_nearest_stations(
        coordinates: NearestStationsSchema,
        session: Session = Depends(get_session),
) -> list[StationModel]:
    if not (-90 <= coordinates.lat <= 90) or not (
            -180 <= coordinates.lng <= 180
    ):
        raise invalid_coordinate_exception()

    return StationModel.read_nearest_stations(
        session=session,
        lat=coordinates.lat,
        lng=coordinates.lng,
        limit=Config.app_nearest_stations_limit,
    )


@router.put(
    "/{station_id}/moderate",
    response_model=StationModerationResponseSchema,
    status_code=status.HTTP_200_OK,
)
def moderate_station(
        station_id: int,
        payload: StationModerationSchema,
        current_user: UserModel = Depends(get_current_user),
        session: Session = Depends(get_session),
):
    """Approve or reject a station. Admin access is required."""
    check_admin_access(current_user)

    station = StationModel.read_station(
        session=session,
        station_id=station_id,
    )

    if station is None:
        raise station_not_found_exception()

    moderation_status = ModerationStatus(payload.moderation_status)

    station.moderation_status = moderation_status

    if moderation_status == ModerationStatus.APPROVED:
        station.rejection_reason = None
    else:
        station.rejection_reason = payload.rejection_reason

    session.commit()
    session.refresh(station)

    return station


@router.get(
    "/{station_id}",
    response_model=StationResponseSchema,
)
def get_station(
        station_id: int,
        session: Session = Depends(get_session),
):
    station = StationModel.read_station(
        session=session,
        station_id=station_id,
    )

    if station is None:
        raise station_not_found_exception()

    return station


@router.put(
    "/{station_id}",
    response_model=StationResponseSchema,
)
def update_station(
        station_id: int,
        payload: StationUpdateSchema,
        current_user: UserModel = Depends(get_current_user),
        session: Session = Depends(get_session),
):
    # Verify existence before checking ownership.
    station = StationModel.read_station(
        session=session,
        station_id=station_id,
    )

    if station is None:
        raise station_not_found_exception()

    check_station_ownership(
        station=station,
        current_user=current_user,
    )

    update_fields = payload.model_dump(exclude_none=True)

    # Re-geocode whenever the address changes.
    if "address" in update_fields:
        try:
            latitude, longitude = geocode_address(
                update_fields["address"]
            )
        except GeocodingError:
            raise geocoding_failed_exception()

        update_fields["latitude"] = latitude
        update_fields["longitude"] = longitude

    try:
        station = StationModel.update_station(
            session=session,
            station_id=station_id,
            **update_fields,
        )

        if station is None:
            raise station_not_found_exception()

        session.commit()
        session.refresh(station)

        return station

    except IntegrityError:
        session.rollback()
        raise duplicate_station_exception()


@router.delete(
    "/{station_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_station(
        station_id: int,
        current_user: UserModel = Depends(get_current_user),
        session: Session = Depends(get_session),
):
    # Verify existence before checking ownership.
    station = StationModel.read_station(
        session=session,
        station_id=station_id,
    )

    if station is None:
        raise station_not_found_exception()

    check_station_ownership(
        station=station,
        current_user=current_user,
    )

    # Soft-delete only after ownership has been verified.
    deleted_station_id = StationModel.delete_station(
        session=session,
        station_id=station_id,
    )

    if deleted_station_id is None:
        raise station_not_found_exception()

    session.commit()

    return None
