"""Unit tests for ChatRoomModel."""

import pytest
from sqlalchemy.exc import IntegrityError

from models.chat_room import ChatRoomModel, ChatRoomStatus
from models.customer import CustomerModel
from models.order import OrderModel
from models.station import StationModel
from models.station_service import StationServiceModel
from models.user import UserModel


def _make_user(db_session, email="chat-owner@example.com"):
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
        name="Chat Test STO",
        address="Chat Test St",
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
    return service


def _make_customer(db_session):
    customer = CustomerModel(
        ip="127.0.0.1",
        device_hash="b" * 36,
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

    order = OrderModel.create_order(
        session=db_session,
        customer_id=customer.id,
        station_id=station.id,
        station_service_id=service.id,
    )
    db_session.commit()

    return order


def test_create_chat_room(db_session):
    order = _make_order(db_session)

    chat_room = ChatRoomModel(
        order_id=order.id,
    )

    db_session.add(chat_room)
    db_session.commit()

    assert chat_room.id is not None
    assert chat_room.order_id == order.id
    assert chat_room.status == ChatRoomStatus.ACTIVE
    assert chat_room.created_at is not None
    assert chat_room.updated_at is not None


def test_chat_room_order_id_must_be_unique(db_session):
    order = _make_order(db_session)

    first_chat_room = ChatRoomModel(
        order_id=order.id,
    )

    db_session.add(first_chat_room)
    db_session.commit()

    second_chat_room = ChatRoomModel(
        order_id=order.id,
    )

    db_session.add(second_chat_room)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_chat_room_requires_existing_order(db_session):
    chat_room = ChatRoomModel(
        order_id=999999,
    )

    db_session.add(chat_room)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()
