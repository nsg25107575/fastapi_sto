"""Unit tests for ChatMessageModel."""

import pytest
from sqlalchemy.exc import IntegrityError

from models.chat_message import ChatMessageModel, MessageType, SenderType
from models.chat_room import ChatRoomModel
from models.customer import CustomerModel
from models.order import OrderModel
from models.station import StationModel
from models.station_service import StationServiceModel
from models.user import UserModel


def _make_user(db_session, email="chat-message-owner@example.com"):
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
        name="Chat Message Test STO",
        address="Chat Message Test St",
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
        device_hash="c" * 36,
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


def _make_chat_room(db_session):
    order = _make_order(db_session)

    chat_room = ChatRoomModel(
        order_id=order.id,
    )
    db_session.add(chat_room)
    db_session.commit()

    return chat_room


def test_create_chat_message(db_session):
    chat_room = _make_chat_room(db_session)

    message = ChatMessageModel(
        chat_room_id=chat_room.id,
        message_type=MessageType.USER,
        sender_type=SenderType.CUSTOMER,
        sender_id=1,
        body="Hello, I would like to ask about the service.",
    )

    db_session.add(message)
    db_session.commit()

    assert message.id is not None
    assert message.chat_room_id == chat_room.id
    assert message.message_type == MessageType.USER
    assert message.sender_type == SenderType.CUSTOMER
    assert message.sender_id == 1
    assert message.body == "Hello, I would like to ask about the service."
    assert message.attachment_url is None
    assert message.created_at is not None


def test_chat_message_requires_existing_chat_room(db_session):
    message = ChatMessageModel(
        chat_room_id=999999,
        message_type=MessageType.USER,
        sender_type=SenderType.CUSTOMER,
        sender_id=1,
        body="Hello",
    )

    db_session.add(message)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_create_multiple_chat_messages(db_session):
    chat_room = _make_chat_room(db_session)

    first_message = ChatMessageModel(
        chat_room_id=chat_room.id,
        message_type=MessageType.USER,
        sender_type=SenderType.CUSTOMER,
        sender_id=1,
        body="Hello",
    )

    second_message = ChatMessageModel(
        chat_room_id=chat_room.id,
        message_type=MessageType.USER,
        sender_type=SenderType.CUSTOMER,
        sender_id=1,
        body="I have a question about the service.",
    )

    db_session.add_all([first_message, second_message])
    db_session.commit()

    assert first_message.id is not None
    assert second_message.id is not None

    assert first_message.id != second_message.id

    assert first_message.chat_room_id == chat_room.id
    assert second_message.chat_room_id == chat_room.id

    assert first_message.body == "Hello"
    assert second_message.body == "I have a question about the service."
