from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.authorization import check_station_permission
from auth.dependencies import get_current_user
from database.engine import get_session
from exceptions.exceptions import (
    service_not_found_exception,
    station_not_found_exception,
)
from models.station import StationModel
from models.station_service import StationServiceModel
from models.user import UserModel
from validations.pagination import PaginatedResponse, PaginationParams
from validations.service import ServiceCreateSchema, ServiceUpdateSchema

router = APIRouter(
    prefix="/services",
    tags=["Services"],
)


@router.post("/", status_code=201)
def create_service(
        payload: ServiceCreateSchema,
        current_user: UserModel = Depends(get_current_user),
        session: Session = Depends(get_session),
):
    """Create a service for a station owned by the current user."""
    try:
        station = StationModel.read_station(session, payload.station_id)

        if station is None:
            raise station_not_found_exception()

        check_station_permission(
            station=station,
            current_user=current_user,
            session=session,
            permission="service.manage",
        )

        service = StationServiceModel.add_service(
            session=session,
            station_id=payload.station_id,
            name=payload.name,
            price=payload.price,
        )

        if service is None:
            raise station_not_found_exception()

        session.commit()
        session.refresh(service)

        return service

    except Exception:
        session.rollback()
        raise


@router.get("/", response_model=PaginatedResponse[str])
def read_services(
        pagination: PaginationParams = Depends(),
        session: Session = Depends(get_session),
):
    """Get a paginated list of unique service names."""
    items, total = StationServiceModel.get_services(
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


@router.get("/{service_id}")
def read_service(
        service_id: int,
        session: Session = Depends(get_session),
):
    """Get a service by its ID."""
    service = StationServiceModel.get_service(
        session=session,
        service_id=service_id,
    )

    if service is None:
        raise service_not_found_exception()

    return service


@router.put("/{service_id}")
def edit_service(
        service_id: int,
        payload: ServiceUpdateSchema,
        current_user: UserModel = Depends(get_current_user),
        session: Session = Depends(get_session),
):
    """Edit a service belonging to a station owned by the current user."""
    try:
        service = StationServiceModel.get_service(
            session=session,
            service_id=service_id,
        )

        if service is None:
            raise service_not_found_exception()

        station = StationModel.read_station(session, service.station_id)

        if station is None:
            raise station_not_found_exception()

        check_station_permission(
            station=station,
            current_user=current_user,
            session=session,
            permission="service.manage",
        )

        update_data = payload.model_dump(exclude_unset=True)

        service = StationServiceModel.update_service(
            session=session,
            service_id=service_id,
            **update_data,
        )

        if service is None:
            raise service_not_found_exception()

        session.commit()
        session.refresh(service)

        return service

    except Exception:
        session.rollback()
        raise


@router.delete("/{service_id}")
def remove_service(
        service_id: int,
        current_user: UserModel = Depends(get_current_user),
        session: Session = Depends(get_session),
):
    """Delete a service belonging to a station owned by the current user."""
    try:
        service = StationServiceModel.get_service(
            session=session,
            service_id=service_id,
        )

        if service is None:
            raise service_not_found_exception()

        station = StationModel.read_station(session, service.station_id)

        if station is None:
            raise station_not_found_exception()

        check_station_permission(
            station=station,
            current_user=current_user,
            session=session,
            permission="service.manage",
        )

        deleted_service_id = StationServiceModel.delete_service(
            session=session,
            service_id=service_id,
        )

        if deleted_service_id is None:
            raise service_not_found_exception()

        session.commit()

        return deleted_service_id

    except Exception:
        session.rollback()
        raise
