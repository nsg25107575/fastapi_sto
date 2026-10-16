"""Order placed by an (anonymous) customer for a specific station's
service, found via GET /stations/nearest.

Deliberately tied to `CustomerModel` (not `UserModel`) -- ordering a
service does not require an account, mirroring the existing anonymous
`/customer` geolocation-capture flow already in this codebase.
"""
import enum
from datetime import datetime
from typing import Self

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, text, select
from sqlalchemy.orm import Mapped, mapped_column, Session, relationship

from database.engine import Base
from exceptions.exceptions import order_customer_id_doesnt_refer_to_customer_exception, \
    service_id_doesnt_belong_to_station_exception
from i18n.dependency_translator import t
from models.chat_message import (ChatMessageModel, MessageType, SenderType)
from models.chat_room import ChatRoomModel, ChatRoomStatus
from models.customer import CustomerModel
from models.station_service import StationServiceModel


class OrderStatus(str, enum.Enum):
    """Lifecycle states of a service order"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    customer_id: Mapped[int] = mapped_column(
        Integer(), ForeignKey("customers.id"), nullable=False
    )
    station_id: Mapped[int] = mapped_column(
        Integer(), ForeignKey("stations.id"), nullable=False
    )
    station_service_id: Mapped[int] = mapped_column(
        Integer(), ForeignKey("station_services.id"), nullable=False
    )
    customer_action_id: Mapped[int | None] = mapped_column(
        Integer(), ForeignKey("customers.id"), server_default=None, nullable=True
    )
    station_action_id: Mapped[int | None] = mapped_column(
        Integer(), ForeignKey("stations.id"), server_default=None, nullable=True
    )

    status: Mapped[OrderStatus] = mapped_column(
        # values_callable is required: without it, SQLAlchemy's Enum type
        # persists/reads the member NAMES ("PENDING", "CONFIRMED", ...),
        # not their .value ("pending", "confirmed", ...) -- but
        # server_default below is set to .value (lowercase). That
        # mismatch made every insert fail with "LookupError: 'pending'
        # is not among the defined enum values" once the server default
        # actually got exercised (i.e. the very first INSERT).
        Enum(OrderStatus, native_enum=False, length=20, values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False, server_default=OrderStatus.PENDING.value,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    __table_args__ = (
        Index("idx_order_station_id", "station_id"),
        Index("idx_order_customer_id", "customer_id"),
        Index("idx_order_status", "status"),
    )

    station = relationship("StationModel", foreign_keys=[station_id])
    customer = relationship("CustomerModel", foreign_keys=[customer_id])
    station_service = relationship("StationServiceModel")

    @property
    def is_new(self) -> bool:
        """True if the order in pending, confirmed or in_progress status."""
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.IN_PROGRESS]

    @property
    def is_cancelled(self) -> bool:
        """True if the order has been canceled by either the customer or the station."""
        return self.status == OrderStatus.CANCELLED

    @property
    def is_rejected(self) -> bool:
        """True if the order has been rejected by either the customer or the station."""
        return self.status == OrderStatus.REJECTED

    @property
    def is_completed(self) -> bool:
        """True if the order has been completed by either the customer or the station."""
        return self.status == OrderStatus.COMPLETED

    @property
    def order_status(self):
        return t(f"order.{self.status.value}")

    @classmethod
    def create_order(
            cls,
            session: Session,
            customer_id: int,
            station_id: int,
            station_service_id: int,
    ) -> Self:
        """
        Create a new order for a customer, pinned to one station and one
        of that station's services. Raises ValueError if the given
        service does not belong to the given station -- ordering a
        service from a different station than the one the customer
        picked (e.g. by sending mismatched ids) is a client error, not
        something that should silently create inconsistent data. Also
        raises ValueError if the customer does not exist, mapped to the
        same 400 response as the station/service mismatch rather than a
        raw IntegrityError from the FK constraint.
        """
        # Validate that the customer exists and that the service belongs to the station.
        if session.get(CustomerModel, customer_id) is None:
            raise order_customer_id_doesnt_refer_to_customer_exception()

        # Validate that the service belongs to the station.
        service = session.get(StationServiceModel, station_service_id)
        if service is None or service.station_id != station_id:
            raise service_id_doesnt_belong_to_station_exception()

        # Create the order, which will be in the default PENDING state.
        order = cls(
            customer_id=customer_id,
            station_id=station_id,
            station_service_id=station_service_id,
        )
        session.add(order)
        session.flush()

        return order

    @classmethod
    def read_order(cls, session: Session, order_id: int) -> Self | None:
        """Find an order by its id. Returns None if it does not exist."""
        return session.get(cls, order_id)

    @classmethod
    def read_orders_by_station(cls, session: Session, station_id: int) -> list[Self]:
        """All orders placed against a given station, newest first."""
        stmt = (
            select(cls)
            .where(cls.station_id == station_id)
            .order_by(cls.created_at.desc())
        )
        return list(session.scalars(stmt).all())

    @classmethod
    def update_order_status(
            cls, session: Session, order_id: int, status: OrderStatus
    ) -> Self | None:
        """Update an order's status. Returns None if the order does not
        exist (caller maps this to a 404)."""
        order = cls.read_order(session, order_id)

        if order is None:
            return None

        old_status = order.status

        if old_status == status:
            return order

        order.status = status

        chat_room = session.query(ChatRoomModel).filter_by(order_id=order_id).one()
        if status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
            chat_room.status = ChatRoomStatus.ARCHIVED

        body = t("order.status_updated", status=order.order_status)

        system_message = ChatMessageModel(
            chat_room_id=chat_room.id,
            message_type=MessageType.SYSTEM,
            sender_type=SenderType.SYSTEM,
            sender_id=None,
            body=body,
        )

        session.add(system_message)
        session.flush()

        return order
