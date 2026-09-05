from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import SessionLocal
from models.station import StationModel

router = APIRouter()


def get_session():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@router.post("/")
def add_station(
        name: str,
        address: str,
        session: Session = Depends(get_session)
):
    try:
        return StationModel.create_station(
            session=session,
            name=name,
            address=address
        )

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Станция с таким названием и адресом уже существует"
        )


@router.get("/{station_id}")
def get_station(
        station_id: int,
        session: Session = Depends(get_session)
):
    station = StationModel.read_station(
        session=session,
        station_id=station_id
    )

    if station is None:
        raise HTTPException(
            status_code=404,
            detail="Станция не найдена"
        )

    return station


@router.get("/")
def get_stations(
        session: Session = Depends(get_session)
):
    return StationModel.read_stations(
        session=session
    )


@router.put("/{station_id}")
def update_station(
        station_id: int,
        name: str | None = None,
        address: str | None = None,
        active: bool | None = None,
        session: Session = Depends(get_session)
):
    station = StationModel.update_station(
        session=session,
        station_id=station_id,
        name=name,
        address=address,
        active=active
    )

    if station is None:
        raise HTTPException(
            status_code=404,
            detail="Станция не найдена"
        )

    return station


@router.delete("/{station_id}")
def delete_station(
        station_id: int,
        session: Session = Depends(get_session)
):
    station = StationModel.delete_station(
        session=session,
        station_id=station_id
    )

    if station is None:
        raise HTTPException(
            status_code=404,
            detail="Станция не найдена"
        )

    return station
