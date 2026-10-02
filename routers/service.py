from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.engine import get_session
from models.station_service import StationServiceModel

router = APIRouter(
    prefix="/services",
    tags=["Services"]
)

# FastAPI endpoints

@router.post(
    "/",
    dependencies=[Depends(get_current_user)]
)
def create_service(
        station_id: int,
        name: str,
        price: float | None = None,
        session: Session = Depends(get_session)
):
    return StationServiceModel.add_service(
        session=session,
        station_id=station_id,
        name=name,
        price=price
    )

@router.get("/")
def read_services(
        session: Session = Depends(get_session)
):
    return StationServiceModel.get_services(
        session=session
    )


@router.get("/{service_id}")
def read_service(
        service_id: int,
        session: Session = Depends(get_session)
):
    service = StationServiceModel.get_service(
        session=session,
        service_id=service_id
    )

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Услуга не найдена"
        )

    return service


@router.put(
    "/{service_id}",
    dependencies=[Depends(get_current_user)]
)
def edit_service(
        service_id: int,
        name: str | None = None,
        price: float | None = None,
        session: Session = Depends(get_session)
):
    service = StationServiceModel.update_service(
        session=session,
        service_id=service_id,
        name=name,
        price=price
    )

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Услуга не найдена"
        )

    return service


@router.delete(
    "/{service_id}",
    dependencies=[Depends(get_current_user)]
)
def remove_service(
        service_id: int,
        session: Session = Depends(get_session)
):
    service = StationServiceModel.delete_service(
        session=session,
        service_id=service_id
    )

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Услуга не найдена"
        )

    return service
