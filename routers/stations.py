from fastapi import APIRouter, Depends, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from config import Config
from database.engine import get_session
from exceptions import DuplicateStationException, GeocodingFailedException, InvalidCoordinateException, \
    StationNotFoundException
from models.station import StationModel
from models.user import UserModel
from services.geocoding import GeocodingError, geocode_address
from validations.pagination import PaginatedResponse, PaginationParams
from validations.station import StationCreateSchema, StationUpdateSchema, StationResponseSchema, \
    NearestStationResponseSchema, NearestStationsSchema

router = APIRouter(
    prefix="/stations",
    tags=["Stations"]
)


@router.post("/", response_model=StationResponseSchema, status_code=status.HTTP_201_CREATED)
def add_station(
        payload: StationCreateSchema,
        current_user: UserModel = Depends(get_current_user),
        session: Session = Depends(get_session)
):
    # Resolve the address to coordinates up front, before touching the
    # DB -- so a geocoding failure never leaves a half-created station
    # (one with a name/address but no lat/lng, invisible to
    # GET /stations/nearest) that a client has no way to retry/fix.
    try:
        latitude, longitude = geocode_address(payload.address)
    except GeocodingError:
        raise GeocodingFailedException

    try:
        station = StationModel.create_station(
            session=session,
            user_id=current_user.id,
            name=payload.name,
            address=payload.address
        )
        station.latitude = latitude
        station.longitude = longitude
        session.commit()
        return station
    except IntegrityError:
        session.rollback()
        raise DuplicateStationException


@router.get("/",
            response_model=PaginatedResponse[StationResponseSchema],
            status_code=status.HTTP_200_OK)
def get_stations(
        pagination: PaginationParams = Depends(),
        session: Session = Depends(get_session)
):
    items, total = StationModel.read_stations(session, pagination.offset, pagination.limit)
    return PaginatedResponse(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


@router.get("/nearest", response_model=list[NearestStationResponseSchema])
def get_nearest_stations(
        coordinates: NearestStationsSchema,
        session: Session = Depends(get_session)
) -> list[StationModel]:
    if not (-90 <= coordinates.lat <= 90) or not (-180 <= coordinates.lng <= 180):
        raise InvalidCoordinateException

    return StationModel.read_nearest_stations(
        session=session, lat=coordinates.lat, lng=coordinates.lng,
        limit=Config.app_nearest_stations_limit
    )


@router.get("/{station_id}", response_model=StationResponseSchema)
def get_station(station_id: int, session: Session = Depends(get_session)):
    station = StationModel.read_station(session=session, station_id=station_id)
    if station is None:
        raise StationNotFoundException
    return station


@router.put("/{station_id}", response_model=StationResponseSchema)
def update_station(
        station_id: int,
        payload: StationUpdateSchema,
        current_user: UserModel = Depends(get_current_user),
        session: Session = Depends(get_session)
):
    update_fields = payload.model_dump(exclude_none=True)

    # Re-geocode whenever the address changes -- otherwise latitude/
    # longitude would silently keep pointing at the OLD address, and
    # GET /stations/nearest would return a station at the wrong location.
    if "address" in update_fields:
        try:
            latitude, longitude = geocode_address(update_fields["address"])
        except GeocodingError:
            raise GeocodingFailedException
        update_fields["latitude"] = latitude
        update_fields["longitude"] = longitude

    try:
        station = StationModel.update_station(
            session=session,
            station_id=station_id,
            **update_fields
        )

        if station is None:
            raise StationNotFoundException

        session.commit()
        return station
    except IntegrityError:
        session.rollback()
        raise DuplicateStationException


@router.delete("/{station_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def delete_station(
        station_id: int,
        current_user: UserModel = Depends(get_current_user),
        session: Session = Depends(get_session)
):
    station = StationModel.delete_station(session=session, station_id=station_id)

    if station is None:
        raise StationNotFoundException

    session.commit()
    return None
