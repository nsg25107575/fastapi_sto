from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.engine import get_session
from exceptions.exceptions import chat_room_archived_exception
from models.chat_message import ChatMessageModel, MessageType, SenderType
from models.chat_room import ChatRoomModel, ChatRoomStatus
from models.customer import CustomerModel
from models.order import OrderModel
from validations.chat import (ChatMessageCreateSchema, ChatMessageResponseSchema)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


def get_owned_chat_room(
        chat_room_id: int,
        customer_device: str | None,
        session: Session,
) -> tuple[CustomerModel, ChatRoomModel]:
    """Find the customer and verify ownership of the chat room."""

    if not customer_device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer cookie is missing",
        )

    customer = session.scalar(
        select(CustomerModel).where(
            CustomerModel.device_hash == customer_device
        )
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer not found",
        )

    chat_room = session.get(ChatRoomModel, chat_room_id)

    if chat_room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found",
        )

    order = session.get(OrderModel, chat_room.order_id)

    if order is None or order.customer_id != customer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this chat room is forbidden",
        )

    return customer, chat_room


@router.post(
    "/rooms/{chat_room_id}/messages",
    response_model=ChatMessageResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_chat_message(
        chat_room_id: int,
        payload: ChatMessageCreateSchema,
        customer_device: str | None = Cookie(default=None),
        session: Session = Depends(get_session),
):
    customer, chat_room = get_owned_chat_room(
        chat_room_id=chat_room_id,
        customer_device=customer_device,
        session=session,
    )

    if chat_room.status == ChatRoomStatus.ARCHIVED:
        raise chat_room_archived_exception()

    message = ChatMessageModel(
        chat_room_id=chat_room.id,
        message_type=MessageType.USER,
        sender_type=SenderType.CUSTOMER,
        sender_id=customer.id,
        body=payload.body,
        attachment_url=payload.attachment_url,
    )

    session.add(message)
    session.commit()
    session.refresh(message)

    return message


@router.get(
    "/rooms/{chat_room_id}/messages",
    response_model=list[ChatMessageResponseSchema],
)
def get_chat_messages(
        chat_room_id: int,
        customer_device: str | None = Cookie(default=None),
        session: Session = Depends(get_session),
):
    _, chat_room = get_owned_chat_room(
        chat_room_id=chat_room_id,
        customer_device=customer_device,
        session=session,
    )

    messages = session.scalars(
        select(ChatMessageModel)
        .where(ChatMessageModel.chat_room_id == chat_room.id)
        .order_by(ChatMessageModel.created_at, ChatMessageModel.id)
    ).all()

    return messages
