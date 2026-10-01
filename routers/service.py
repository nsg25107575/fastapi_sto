
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.engine import get_session
from models.station_service import StationServiceModel

router = APIRouter()

# =========================
# Database functions
# =========================

def add_service(
        session: Session,
        station_id: int,
        name: str,
        price: float | None = None
):
    service = StationServiceModel(
        station_id=station_id,
        name=name,
        price=price
    )

    session.add(service)
    session.commit()
    session.refresh(service)

    return service

def update_service(
        session: Session,
        service_id: int,
        name: str | None = None,
        price: float | None = None
):
    service = session.get(
        StationServiceModel,
        service_id
    )

    if service is None:
        return None

    if name is not None:
        service.name = name

    if price is not None:
        service.price = price

    session.commit()
    session.refresh(service)

    return service

def delete_service(
        session: Session,
        service_id: int
):
    service = session.get(
        StationServiceModel,
        service_id
    )

    if service is None:
        return None

    session.delete(service)
    session.commit()

    return service_id

def get_service(
        session: Session,
        service_id: int
):
    return session.get(
        StationServiceModel,
        service_id
    )

def get_services(session: Session):
    rows = session.query(
        StationServiceModel.name,
        func.min(StationServiceModel.price).label("min_price"),
        func.max(StationServiceModel.price).label("max_price")
    ).group_by(
        StationServiceModel.name
    ).order_by(
        func.min(StationServiceModel.price).desc()
    ).all()

    return [
        {
            "name": row.name,
            "min_price": row.min_price,
            "max_price": row.max_price
        }
        for row in rows
    ]

# =========================
# FastAPI endpoints
# =========================

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
    return add_service(
        session=session,
        station_id=station_id,
        name=name,
        price=price
    )

@router.get("/")
def read_services(
        session: Session = Depends(get_session)
):
    return get_services(
        session=session
    )

@router.get("/{service_id}")
def read_service(
        service_id: int,
        session: Session = Depends(get_session)
):
    service = get_service(
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
    service = update_service(
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
    service = delete_service(
        session=session,
        service_id=service_id
    )

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Услуга не найдена"
        )

    return service

