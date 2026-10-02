"""Unit tests for OrderModel -- customer places an order for a station
service after finding it via GET /stations/nearest.
"""
import pytest

from models.customer import CustomerModel
from models.order import OrderModel, OrderStatus
from models.station import StationModel
from models.station_service import StationServiceModel
from models.user import UserModel


def _make_user(db_session, email="owner@example.com"):
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


def _make_station(db_session, user_id, lat=50.4501, lng=30.5234):
    station = StationModel.create_station(
        session=db_session,
        user_id=user_id,
        name="Order Test STO",
        address="Order Test St",
    )
    station.latitude = lat
    station.longitude = lng
    db_session.commit()
    return station


def _make_service(db_session, station_id, price=250.0):
    service = StationServiceModel.add_service(
        session=db_session,
        station_id=station_id,
        name="Oil change",
        price=price,
    )
    return service


def _make_customer(db_session, lat=50.4501, lng=30.5234):
    customer = CustomerModel(
        ip="127.0.0.1",
        device_hash="a" * 36,
        lat=lat,
        lng=lng,
        public_data={},
    )
    db_session.add(customer)
    db_session.commit()
    return customer


def test_create_order_success(db_session):
    user = _make_user(db_session)
    station = _make_station(db_session, user.id)
    service = _make_service(db_session, station.id)
    customer = _make_customer(db_session)

    order = OrderModel.create_order(
        session=db_session,
        customer_id=customer.id,
        station_id=station.id,
        station_service_id=service.id,
    )
    db_session.commit()

    assert order.id is not None
    assert order.status == OrderStatus.PENDING
    assert order.customer_id == customer.id
    assert order.station_id == station.id
    assert order.station_service_id == service.id


def test_create_order_rejects_service_from_a_different_station(db_session):
    user = _make_user(db_session)
    station_a = _make_station(db_session, user.id, lat=50.4501, lng=30.5234)
    station_a.name, station_a.address = "Station A", "Address A"
    db_session.commit()

    station_b = StationModel.create_station(
        session=db_session, user_id=user.id, name="Station B", address="Address B"
    )
    db_session.commit()

    service_on_b = _make_service(db_session, station_b.id)
    customer = _make_customer(db_session)

    with pytest.raises(ValueError):
        OrderModel.create_order(
            session=db_session,
            customer_id=customer.id,
            station_id=station_a.id,
            station_service_id=service_on_b.id,
        )


def test_read_order(db_session):
    user = _make_user(db_session)
    station = _make_station(db_session, user.id)
    service = _make_service(db_session, station.id)
    customer = _make_customer(db_session)

    created = OrderModel.create_order(
        session=db_session,
        customer_id=customer.id,
        station_id=station.id,
        station_service_id=service.id,
    )
    db_session.commit()

    fetched = OrderModel.read_order(db_session, created.id)

    assert fetched is not None
    assert fetched.id == created.id


def test_read_order_not_found_returns_none(db_session):
    assert OrderModel.read_order(db_session, 999999) is None


def test_update_order_status(db_session):
    user = _make_user(db_session)
    station = _make_station(db_session, user.id)
    service = _make_service(db_session, station.id)
    customer = _make_customer(db_session)

    order = OrderModel.create_order(
        session=db_session,
        customer_id=customer.id,
        station_id=station.id,
        station_service_id=service.id,
    )
    db_session.commit()

    updated = OrderModel.update_order_status(
        session=db_session, order_id=order.id, status=OrderStatus.CONFIRMED
    )
    db_session.commit()

    assert updated.status == OrderStatus.CONFIRMED


def test_update_order_status_not_found_returns_none(db_session):
    result = OrderModel.update_order_status(
        session=db_session, order_id=999999, status=OrderStatus.CONFIRMED
    )

    assert result is None


def test_read_orders_by_station(db_session):
    user = _make_user(db_session)
    station = _make_station(db_session, user.id)
    service = _make_service(db_session, station.id)
    customer = _make_customer(db_session)

    OrderModel.create_order(
        session=db_session,
        customer_id=customer.id,
        station_id=station.id,
        station_service_id=service.id,
    )
    db_session.commit()

    orders = OrderModel.read_orders_by_station(db_session, station.id)

    assert len(orders) == 1
    assert orders[0].station_id == station.id
