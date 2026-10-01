from fastapi import APIRouter, Depends, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user, get_session
from config import Config
from exceptions import DuplicateStationException, InvalidCoordinateException, StationNotFoundException
from models.station import StationModel
from models.user import UserModel
from validation.station import StationCreateSchema, StationUpdateSchema, StationResponseSchema, \
    NearestStationResponseSchema

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
    try:
        station = StationModel.create_station(
            session=session,
            name=payload.name,
            address=payload.address
        )
        session.commit()
        return station
    except IntegrityError:
        session.rollback()
        raise DuplicateStationException


@router.get("/", response_model=list[StationResponseSchema], status_code=status.HTTP_200_OK)
def get_stations(session: Session = Depends(get_session)):
    return StationModel.read_stations(session=session)


@router.get("/nearest", response_model=list[NearestStationResponseSchema])
def get_nearest_stations(lat: float, lng: float, session: Session = Depends(get_session)) -> list[StationModel]:
    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        raise InvalidCoordinateException
    return StationModel.read_nearest_stations(
        session=session, lat=lat, lng=lng,
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
    try:
        # Pass a dictionary with parameters via **kwargs
        station = StationModel.update_station(
            session=session,
            station_id=station_id,
            **payload.model_dump(exclude_none=True)  # Uses dynamic updates from model
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
