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


def generate_device_hash(length: int = 20) -> str:
    characters = string.ascii_letters + string.digits

    return "".join(
        secrets.choice(characters)
        for _ in range(length)
    )


@router.post(
    "/",
    response_model=CustomerResponse,
    description="""
Створення Customer.
 Для автоматичного визначення координат:
[Визначити моє місце знаходження](/location/)
після цього повертаємося в Swagger.
"""
)
def create_customer(
        customer: CustomerCreate,
        request: Request,
        session: Session = Depends(get_session),
):
    client_ip = request.client.host

    device_hash = generate_device_hash()

    new_customer = CustomerModel(
        ip=client_ip,
        device_hash=device_hash,
        lat=customer.lat,
        lng=customer.lng,
    )

    session.add(new_customer)
    session.commit()
    session.refresh(new_customer)

    return new_customer
