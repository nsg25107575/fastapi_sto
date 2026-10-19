from fastapi import APIRouter, Depends, status, Cookie
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.authorization import check_station_permission
from auth.dependencies import get_current_user, get_optional_current_user
from database.engine import get_session
from exceptions import (
    customer_cookie_missing_exception,
    invalid_auth_cookie_exception,
    invalid_order_service_exception,
    order_forbidden_exception,
    order_not_found_exception,
)
from models.customer import CustomerModel
from models.order import OrderModel
from models.user import UserModel
from validations.order import OrderCreateSchema, OrderResponseSchema, OrderStatusUpdateSchema

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)

@router.post("/", response_model=OrderResponseSchema, status_code=status.HTTP_201_CREATED)
def create_order(
        payload: OrderCreateSchema,
        session: Session = Depends(get_session)
):
    """
    Place an order for a station service. Not authenticated -- the
    customer flow (POST /customer -> GET /stations/nearest -> POST
    /orders) is anonymous, same as /customer itself.
    """
    try:
        order = OrderModel.create_order(
            session=session,
            customer_id=payload.customer_id,
            station_id=payload.station_id,
            station_service_id=payload.station_service_id,
        )
        session.commit()
        return order
    except ValueError:
        session.rollback()
        raise invalid_order_service_exception()


@router.get("/{order_id}", response_model=OrderResponseSchema)
def get_order(
        order_id: int,
        customer_device: str | None = Cookie(default=None),
        station: str | None = Cookie(default=None),
        current_user: UserModel | None = Depends(get_optional_current_user),
        session: Session = Depends(get_session),
):
    order = OrderModel.read_order(
        session=session,
        order_id=order_id,
    )

    if order is None:
        raise order_not_found_exception()

    # A supplied station cookie must not silently fall back to anonymous access.
    if station and current_user is None:
        raise invalid_auth_cookie_exception()

    # Station owner or employee with order.manage permission.
    if current_user is not None:
        check_station_permission(
            station=order.station,
            current_user=current_user,
            session=session,
            permission="order.manage",
        )
        return order

    # Anonymous customer: only their own order.
    if not customer_device:
        raise customer_cookie_missing_exception()

    customer = session.scalar(
        select(CustomerModel).where(
            CustomerModel.device_hash == customer_device
        )
    )

    if customer is None:
        raise customer_not_found_unauthorized_exception()

    if order.customer_id != customer.id:
        raise order_forbidden_exception()

    return order


@router.put("/{order_id}/status", response_model=OrderResponseSchema)
def update_order_status(
        order_id: int,
        payload: OrderStatusUpdateSchema,
        current_user: UserModel = Depends(get_current_user),
        session: Session = Depends(get_session),
):
    order = OrderModel.read_order(
        session=session,
        order_id=order_id,
    )

    if order is None:
        raise order_not_found_exception()

    check_station_permission(
        station=order.station,
        current_user=current_user,
        session=session,
        permission="order.manage",
    )

    order = OrderModel.update_order_status(
        session=session,
        order_id=order_id,
        status=payload.status,
    )

    session.commit()
    return order
