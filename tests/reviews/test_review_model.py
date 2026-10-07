import pytest
from fastapi.exceptions import HTTPException

from models.customer import CustomerModel
from models.order import OrderModel
from models.review import ReviewModel
from models.station import StationModel
from models.station_service import StationServiceModel
from models.user import UserModel


def _make_user(db_session, email="review-owner@example.com"):
    user = UserModel.create_user(
        email=email,
        password="StrongPass1!",
        first_name="Owner",
        second_name=None,
        last_name="User",
        session=db_session,
    )
    db_session.commit()
    return user


def _make_station(db_session, user_id):
    station = StationModel.create_station(
        session=db_session,
        user_id=user_id,
        name="Review Test STO",
        address="Review Test St",
    )
    station.latitude = 50.4501
    station.longitude = 30.5234
    db_session.commit()
    return station


def _make_service(db_session, station_id):
    service = StationServiceModel.add_service(
        session=db_session,
        station_id=station_id,
        name="Oil change",
        price=250.0,
    )
    db_session.commit()
    return service


def _make_customer(db_session, device_hash="a" * 36):
    customer = CustomerModel(
        ip="127.0.0.1",
        device_hash=device_hash,
        lat=50.4501,
        lng=30.5234,
        public_data={},
    )
    db_session.add(customer)
    db_session.commit()
    return customer


def _make_order(db_session, station, service, customer):
    return OrderModel.create_order(
        session=db_session,
        customer_id=customer.id,
        station_id=station.id,
        station_service_id=service.id,
    )


def test_create_review_success(db_session):
    user = _make_user(db_session)
    station = _make_station(db_session, user.id)
    service = _make_service(db_session, station.id)
    customer = _make_customer(db_session)

    order = _make_order(db_session, station, service, customer)

    review = ReviewModel.create_review(
        session=db_session,
        order_id=order.id,
        station_id=station.id,
        customer_id=customer.id,
        rating=5,
    )
    assert review is not None


@pytest.mark.parametrize("rating", [0, -1, 6, 10])
def test_create_review_rejects_invalid_rating(
        db_session,
        rating,
):
    user = _make_user(db_session)
    station = _make_station(db_session, user.id)
    service = _make_service(db_session, station.id)
    customer = _make_customer(db_session)

    order = _make_order(db_session, station, service, customer)

    with pytest.raises(HTTPException) as exc_info:
        ReviewModel.create_review(
            session=db_session,
            order_id=order.id,
            station_id=station.id,
            customer_id=customer.id,
            rating=rating,
        )

    assert exc_info.value.status_code == 400


def test_create_review_rejects_unknown_order(db_session):
    with pytest.raises(HTTPException) as exc_info:
        ReviewModel.create_review(
            session=db_session,
            order_id=999999,
            station_id=1,
            customer_id=1,
            rating=5,
        )
    assert exc_info.value.status_code == 404


def test_create_review_rejects_duplicate_order(db_session):
    user = _make_user(db_session)
    station = _make_station(db_session, user.id)
    service = _make_service(db_session, station.id)
    customer = _make_customer(db_session)

    order = _make_order(db_session, station, service, customer)

    ReviewModel.create_review(
        session=db_session,
        order_id=order.id,
        station_id=station.id,
        customer_id=customer.id,
        rating=5,
    )

    with pytest.raises(HTTPException) as exc_info:
        ReviewModel.create_review(
            session=db_session,
            order_id=order.id,
            station_id=station.id,
            customer_id=customer.id,
            rating=4,
        )
    assert exc_info.value.status_code == 400
