import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, text
from sqlalchemy.orm import Mapped, mapped_column

from database.engine import Base


class ChatRoomStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ChatRoomModel(Base):
    __tablename__ = "chat_rooms"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    order_id: Mapped[int] = mapped_column(
        Integer(),
        ForeignKey("orders.id"),
        nullable=False,
        unique=True,
    )

    status: Mapped[ChatRoomStatus] = mapped_column(
        Enum(
            ChatRoomStatus,
            native_enum=False,
            length=10,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        server_default=ChatRoomStatus.ACTIVE.value,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
