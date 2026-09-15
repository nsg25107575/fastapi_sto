import secrets
import string

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from database import SessionLocal
from models.customer import CustomerModel
from schemas.customer import CustomerCreate, CustomerResponse

router = APIRouter(
    prefix="/customer",
    tags=["Customer"],
)


def get_session():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


def generate_device_hash(length: int = 36) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(secrets.choice(characters) for _ in range(length))


@router.post(
    "/",
    response_model=CustomerResponse,
    description="""
    <a id="customer-data-link" href="/location" target="_blank" rel="noopener noreferrer">
        Get location
    </a>
    """
)
def create_customer(
        customer: CustomerCreate,
        request: Request,
        session: Session = Depends(get_session),
):
    ip = request.client.host
    device_hash = generate_device_hash()

    new_customer = CustomerModel(
        ip=ip,
        device_hash=device_hash,
        lat=customer.lat,
        lng=customer.lng,
        public_data=customer.public_data,
    )

    session.add(new_customer)
    session.commit()
    session.refresh(new_customer)

    return new_customer
