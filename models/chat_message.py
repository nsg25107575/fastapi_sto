import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from database.engine import Base


class MessageType(str, enum.Enum):
    SYSTEM = "system"
    USER = "user"


class SenderType(str, enum.Enum):
    CUSTOMER = "customer"
    STATION = "station"
    SYSTEM = "system"


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    chat_room_id: Mapped[int] = mapped_column(
        Integer(),
        ForeignKey("chat_rooms.id"),
        nullable=False,
    )

    message_type: Mapped[MessageType] = mapped_column(
        Enum(
            MessageType,
            native_enum=False,
            length=10,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )

    sender_type: Mapped[SenderType] = mapped_column(
        Enum(
            SenderType,
            native_enum=False,
            length=10,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )

    sender_id: Mapped[int | None] = mapped_column(
        Integer(),
        nullable=True,
    )

    body: Mapped[str] = mapped_column(
        Text(),
        nullable=False,
    )

    attachment_url: Mapped[str | None] = mapped_column(
        Text(),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
