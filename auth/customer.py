from fastapi import Cookie, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.engine import get_session
from models.customer import CustomerModel


def get_current_customer(
        customer_device: str | None = Cookie(default=None),
        session: Session = Depends(get_session),
) -> CustomerModel:
    if not customer_device:
        raise ValueError("Customer cookie is missing")

    customer = session.scalar(
        select(CustomerModel).where(
            CustomerModel.device_hash == customer_device
        )
    )

    if customer is None:
        raise ValueError("Customer not found")

    return customer
