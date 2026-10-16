"""Unit tests for OrderModel."""

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from config import Config
from i18n.dependency_translator import t
from models.chat_message import ChatMessageModel, MessageType, SenderType
from models.chat_room import ChatRoomModel, ChatRoomStatus
from models.customer import CustomerModel
from models.order import OrderModel, OrderStatus
from models.station import StationModel
from models.station_service import StationServiceModel
from models.user import UserModel


def _make_user(db_session, email="order-owner@example.com"):
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
        name="Test STO",
        address="Test Street",
    )
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


def _make_customer(db_session):
    customer = CustomerModel(
        ip="127.0.0.1",
        device_hash="a" * 36,
        lat=50.4501,
        lng=30.5234,
        public_data={},
    )
    db_session.add(customer)
    db_session.commit()
    return customer


def _make_order(db_session):
    user = _make_user(db_session)
    station = _make_station(db_session, user.id)
    service = _make_service(db_session, station.id)
    customer = _make_customer(db_session)

    return OrderModel.create_order(
        session=db_session,
        customer_id=customer.id,
        station_id=station.id,
        station_service_id=service.id,
    )


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

    assert order.id is not None
    assert order.customer_id == customer.id
    assert order.station_id == station.id
    assert order.station_service_id == service.id
    assert order.status == OrderStatus.PENDING
    assert order.created_at is not None
    assert order.updated_at is not None


def test_create_order_creates_chat_room(db_session):
    order = _make_order(db_session)
    db_session.commit()

    chat_room = db_session.scalar(
        select(ChatRoomModel).where(
            ChatRoomModel.order_id == order.id
        )
    )

    assert chat_room is not None
    assert chat_room.id is not None
    assert chat_room.order_id == order.id


def test_create_order_rejects_service_from_a_different_station(db_session):
    user = _make_user(db_session)
    first_station = _make_station(db_session, user.id)
    second_station = StationModel.create_station(
        session=db_session,
        user_id=user.id,
        name="Second Test STO",
        address="Second Test Street",
    )
    db_session.commit()

    service = _make_service(db_session, first_station.id)
    customer = _make_customer(db_session)

    with pytest.raises(HTTPException) as exc_info:
        OrderModel.create_order(
            session=db_session,
            customer_id=customer.id,
            station_id=second_station.id,
            station_service_id=service.id,
        )
    assert exc_info.value.status_code == 400


def test_read_order(db_session):
    order = _make_order(db_session)
    db_session.commit()

    result = OrderModel.read_order(
        session=db_session,
        order_id=order.id,
    )

    assert result is not None
    assert result.id == order.id
    assert result.customer_id == order.customer_id
    assert result.station_id == order.station_id
    assert result.station_service_id == order.station_service_id


def test_read_order_not_found_returns_none(db_session):
    result = OrderModel.read_order(
        session=db_session,
        order_id=999999,
    )

    assert result is None


def test_update_order_status(db_session):
    order = _make_order(db_session)
    db_session.commit()

    result = OrderModel.update_order_status(
        session=db_session,
        order_id=order.id,
        status=OrderStatus.CONFIRMED,
    )
    db_session.commit()

    assert result is not None
    assert result.id == order.id
    assert result.status == OrderStatus.CONFIRMED


def test_update_order_status_creates_system_message(db_session):
    order = _make_order(db_session)
    db_session.commit()

    result = OrderModel.update_order_status(
        session=db_session,
        order_id=order.id,
        status=OrderStatus.CONFIRMED,
    )
    db_session.commit()

    assert result is not None
    assert result.status == OrderStatus.CONFIRMED

    chat_room = db_session.scalar(
        select(ChatRoomModel).where(
            ChatRoomModel.order_id == order.id
        )
    )

    assert chat_room is not None

    message = db_session.scalar(
        select(ChatMessageModel).where(
            ChatMessageModel.chat_room_id == chat_room.id
        )
    )

    assert message is not None
    assert message.message_type == MessageType.SYSTEM
    assert message.sender_type == SenderType.SYSTEM
    assert message.sender_id is None
    assert message.body == t(
        "order.status_updated",
        locale=Config.app_default_locale,
        status=t(
            f"order.{result.status.value}",
            locale=Config.app_default_locale,
        ),
    )


def test_update_order_status_does_not_create_message_for_same_status(
        db_session,
):
    order = _make_order(db_session)
    db_session.commit()

    result = OrderModel.update_order_status(
        session=db_session,
        order_id=order.id,
        status=OrderStatus.PENDING,
    )
    db_session.commit()

    assert result is not None
    assert result.status == OrderStatus.PENDING

    chat_room = db_session.scalar(
        select(ChatRoomModel).where(
            ChatRoomModel.order_id == order.id
        )
    )

    assert chat_room is not None

    messages = list(
        db_session.scalars(
            select(ChatMessageModel).where(
                ChatMessageModel.chat_room_id == chat_room.id
            )
        ).all()
    )

    assert messages == []


def test_update_order_status_not_found_returns_none(db_session):
    result = OrderModel.update_order_status(
        session=db_session,
        order_id=999999,
        status=OrderStatus.CONFIRMED,
    )

    assert result is None


def test_read_orders_by_station(db_session):
    user = _make_user(db_session)
    station = _make_station(db_session, user.id)
    service = _make_service(db_session, station.id)

    customer_one = _make_customer(db_session)

    customer_two = CustomerModel(
        ip="127.0.0.2",
        device_hash="c" * 36,
        lat=50.4502,
        lng=30.5235,
        public_data={},
    )
    db_session.add(customer_two)
    db_session.commit()

    first_order = OrderModel.create_order(
        session=db_session,
        customer_id=customer_one.id,
        station_id=station.id,
        station_service_id=service.id,
    )

    second_order = OrderModel.create_order(
        session=db_session,
        customer_id=customer_two.id,
        station_id=station.id,
        station_service_id=service.id,
    )

    db_session.commit()

    orders = OrderModel.read_orders_by_station(
        session=db_session,
        station_id=station.id,
    )

    assert len(orders) == 2
    assert {order.id for order in orders} == {
        first_order.id,
        second_order.id,
    }
    assert orders[0].created_at >= orders[1].created_at


@pytest.mark.parametrize(
    "status",
    [OrderStatus.COMPLETED, OrderStatus.CANCELLED],
)
def test_update_order_status_archives_chat_room(db_session, status):
    order = _make_order(db_session)
    db_session.commit()

    result = OrderModel.update_order_status(
        session=db_session,
        order_id=order.id,
        status=status,
    )
    db_session.commit()

    assert result is not None
    assert result.status == status

    chat_room = db_session.scalar(
        select(ChatRoomModel).where(
            ChatRoomModel.order_id == order.id
        )
    )

    assert chat_room is not None
    assert chat_room.status == ChatRoomStatus.ARCHIVED
