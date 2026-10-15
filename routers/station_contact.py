from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from auth.authorization import check_station_ownership
from auth.dependencies import get_current_user
from database.engine import get_session
from exceptions.exceptions import (
    station_contact_not_found_exception,
    station_not_found_exception,
)
from models.station import StationModel
from models.station_contact import StationContactModel
from models.user import UserModel
from validations.pagination import PaginatedResponse, PaginationParams
from validations.station_contact import (
    StationContactCreateSchema,
    StationContactResponseSchema,
    StationContactUpdateSchema,
)

router = APIRouter(
    prefix="/station-contacts",
    tags=["Station Contacts"],
)


@router.post(
    "/",
    response_model=StationContactResponseSchema,
    status_code=201,
)
def create_station_contact(
        contact_data: StationContactCreateSchema,
        current_user: UserModel = Depends(get_current_user),
        session: Session = Depends(get_session),
):
    """Create a contact for a station owned by the current user."""
    try:
        station = StationModel.read_station(
            session,
            contact_data.station_id,
        )

        if station is None:
            raise station_not_found_exception()

        check_station_ownership(station, current_user)

        contact = StationContactModel(
            station_id=contact_data.station_id,
            type=contact_data.type,
            value=contact_data.value,
        )

        session.add(contact)
        session.commit()
        session.refresh(contact)

        return contact

    except Exception:
        session.rollback()
        raise


@router.get(
    "/",
    response_model=PaginatedResponse[StationContactResponseSchema],
)
def read_station_contacts(
        station_id: int | None = Query(default=None, gt=0),
        pagination: PaginationParams = Depends(),
        session: Session = Depends(get_session),
):
    """Get a paginated list of station contacts."""
    query = select(StationContactModel)

    if station_id is not None:
        query = query.where(
            StationContactModel.station_id == station_id
        )

    total_query = select(func.count()).select_from(query.subquery())
    total = session.scalar(total_query) or 0

    contacts = session.scalars(
        query
        .order_by(StationContactModel.id)
        .offset(pagination.offset)
        .limit(pagination.limit)
    ).all()

    return PaginatedResponse(
        items=contacts,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get(
    "/{contact_id}",
    response_model=StationContactResponseSchema,
)
def read_station_contact(
        contact_id: int,
        session: Session = Depends(get_session),
):
    """Get a station contact by ID."""
    contact = session.get(StationContactModel, contact_id)

    if contact is None:
        raise station_contact_not_found_exception()

    return contact


@router.put(
    "/{contact_id}",
    response_model=StationContactResponseSchema,
)
def update_station_contact(
        contact_id: int,
        contact_data: StationContactUpdateSchema,
        current_user: UserModel = Depends(get_current_user),
        session: Session = Depends(get_session),
):
    """Update a contact belonging to a station owned by the current user."""
    try:
        contact = session.get(StationContactModel, contact_id)

        if contact is None:
            raise station_contact_not_found_exception()

        station = StationModel.read_station(
            session,
            contact.station_id,
        )

        if station is None:
            raise station_not_found_exception()

        check_station_ownership(station, current_user)

        update_data = contact_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if value is not None:
                setattr(contact, field, value)

        contact.updated_at = datetime.now()

        session.commit()
        session.refresh(contact)

        return contact

    except Exception:
        session.rollback()
        raise


@router.delete("/{contact_id}")
def delete_station_contact(
        contact_id: int,
        current_user: UserModel = Depends(get_current_user),
        session: Session = Depends(get_session),
):
    """Delete a contact belonging to a station owned by the current user."""
    try:
        contact = session.get(StationContactModel, contact_id)

        if contact is None:
            raise station_contact_not_found_exception()

        station = StationModel.read_station(
            session,
            contact.station_id,
        )

        if station is None:
            raise station_not_found_exception()

        check_station_ownership(station, current_user)

        session.delete(contact)
        session.commit()

        return {"id": contact_id}

    except Exception:
        session.rollback()
        raise
