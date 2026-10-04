from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, Index, text, Numeric, select
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from database.engine import Base
from database.pagination import paginate

if TYPE_CHECKING:
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
        """
        Add a new service to a station.
        """
        service = cls(
            station_id=station_id,
            name=name,
            price=price
        )

        session.add(service)
        session.commit()
        session.refresh(service)

        return service

    @classmethod
    def update_service(cls, session: Session, service_id: int, name: str | None = None, price: float | None = None):
        """
        Update a service by its ID. Only provided fields will be updated.
        """
        service = session.get(cls, service_id)
        if service is None:
            return None

        if name is not None:
            service.name = name
        if price is not None:
            service.price = price

        session.commit()
        session.refresh(service)

        return service

    @classmethod
    def delete_service(cls, session: Session, service_id: int):
        """
        Delete a service by its ID.
        """
        service = session.get(cls, service_id)
        if service is None:
            return None

        session.delete(service)
        session.commit()

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
