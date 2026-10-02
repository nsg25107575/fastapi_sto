from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.engine import get_session
from exceptions import InvalidOrderServiceException, OrderNotFoundException
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
        raise InvalidOrderServiceException


@router.get("/{order_id}", response_model=OrderResponseSchema)
def get_order(order_id: int, session: Session = Depends(get_session)):
    order = OrderModel.read_order(session=session, order_id=order_id)
    if order is None:
        raise OrderNotFoundException
    return order


@router.put("/{order_id}/status", response_model=OrderResponseSchema)
def update_order_status(
        order_id: int,
        payload: OrderStatusUpdateSchema,
        current_user: UserModel = Depends(get_current_user),
        session: Session = Depends(get_session)
):
    """
    Update an order's status (e.g. a station owner confirming or
    rejecting an incoming order). Requires authentication -- unlike
    order creation, which stays anonymous.

    Ownership is NOT yet enforced (any authenticated user can update
    any order's status) -- consistent with the existing, already-known
    gap on PUT/DELETE /stations/{id} (see docs/ISSUES.md ISSUE-2);
    tracked for a follow-up pass once a shared authorization layer is
    added for both.
    """
    order = OrderModel.update_order_status(
        session=session, order_id=order_id, status=payload.status
    )
    if order is None:
        raise OrderNotFoundException

    session.commit()
    return order
