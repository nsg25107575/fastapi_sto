from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.engine import get_session
from exceptions.exceptions import service_not_found_exception
from models.station_service import StationServiceModel
from validations.pagination import PaginatedResponse, PaginationParams

router = APIRouter(
    prefix="/services",
    tags=["Services"]
)


@router.post("/", dependencies=[Depends(get_current_user)])
def create_service(station_id: int, name: str, price: float | None = None, session: Session = Depends(get_session)):
    """
    Create a new service for a station
    """
    return StationServiceModel.add_service(
        session=session,
        station_id=station_id,
        name=name,
        price=price
    )


@router.get("/", response_model=PaginatedResponse[str])
def read_services(pagination: PaginationParams = Depends(), session: Session = Depends(get_session)):
    """
    Get a list of all unique services
    """
    items, total = StationServiceModel.get_services(session, pagination.offset, pagination.limit)

    return PaginatedResponse(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


@router.get("/{service_id}")
def read_service(service_id: int, session: Session = Depends(get_session)):
    """
    Get a service by its ID
    """
    service = StationServiceModel.get_service(
        session=session,
        service_id=service_id
    )

    if service is None:
        raise service_not_found_exception()

    return service


@router.put("/{service_id}", dependencies=[Depends(get_current_user)])
def edit_service(
        service_id: int,
        name: str | None = None,
        price: float | None = None,
        session: Session = Depends(get_session)
):
    """
    Edit an existing service
    """
    service = StationServiceModel.update_service(
        session=session,
        service_id=service_id,
        name=name,
        price=price
    )

    if service is None:
        raise service_not_found_exception()

    return service


@router.delete("/{service_id}", dependencies=[Depends(get_current_user)])
def remove_service(service_id: int, session: Session = Depends(get_session)):
    """
    Remove a service by its ID
    """
    service = StationServiceModel.delete_service(
        session=session,
        service_id=service_id
    )

    if service is None:
        raise service_not_found_exception()

    return service
