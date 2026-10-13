from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Index, text, Numeric, select
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from database.engine import Base
from database.pagination import paginate
from models.station import StationModel


class StationServiceModel(Base):
    """
    Represents a service offered by a station, including its name and price.
    """
    __tablename__ = "station_services"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    station_id: Mapped[int] = mapped_column(
        ForeignKey("stations.id"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    price: Mapped[float | None] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP")
    )

    __table_args__ = (
        Index(
            "idx_station_service_name",
            "name"
        ),
    )

    # Feedback to the station model
    station: Mapped["StationModel"] = relationship(back_populates="services")

    @classmethod
    def add_service(cls, session: Session, station_id: int, name: str, price: float | None = None):
        """Add a service and reset the parent station moderation status."""
        station = session.get(StationModel, station_id)

        if station is None:
            return None

        service = cls(station_id=station_id, name=name, price=price)

        station.moderation_status = "pending"

        session.add(service)
        session.flush()
        session.refresh(service)

        return service

    @classmethod
    def update_service(
            cls,
            session: Session,
            service_id: int,
            name: str | None = None,
            price: float | None = None,
    ):
        """Update a service and reset moderation when its data changes."""
        service = session.get(cls, service_id)

        if service is None:
            return None

        station = session.get(StationModel, service.station_id)

        if station is None:
            return None

        changed = False

        if name is not None and service.name != name:
            service.name = name
            changed = True

        if price is not None and service.price != price:
            service.price = price
            changed = True

        if changed:
            station.moderation_status = "pending"

        session.flush()
        session.refresh(service)

        return service

    @classmethod
    def delete_service(cls, session: Session, service_id: int):
        """Delete a service and reset the parent station moderation status."""
        service = session.get(cls, service_id)

        if service is None:
            return None

        station = session.get(StationModel, service.station_id)

        if station is None:
            return None

        station.moderation_status = "pending"

        session.delete(service)
        session.flush()

        return service_id

    @classmethod
    def get_service(cls, session: Session, service_id: int):
        """
        Get a service by its ID.
        """
        return session.get(cls, service_id)

    @classmethod
    def get_services(cls, session: Session, offset: int = 0, limit: int = 20) -> tuple[list[str], int]:
        """
        Returns a page of distinct service names, for autocomplete when a
        station owner is typing a new service name (so they don't invent
        slightly different names for the same service).
        """
        stmt = select(cls.name).distinct().order_by(cls.name)
        return paginate(session, stmt, offset, limit)
