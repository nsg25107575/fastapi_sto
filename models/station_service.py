from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, Index, text, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from database.engine import Base

if TYPE_CHECKING:
    from models.station import StationModel


class StationServiceModel(Base):
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
    def add_service(
            cls,
            session: Session,
            station_id: int,
            name: str,
            price: float | None = None
    ):
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
    def update_service(
            cls,
            session: Session,
            service_id: int,
            name: str | None = None,
            price: float | None = None
    ):
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
    def delete_service(
            cls,
            session: Session,
            service_id: int
    ):
        service = session.get(cls, service_id)
        if service is None:
            return None

        session.delete(service)
        session.commit()
        return service_id

    @classmethod
    def get_service(
            cls,
            session: Session,
            service_id: int
    ):
        return session.get(cls, service_id)

    @classmethod
    def get_services(cls, session: Session):
        rows = session.query(
            cls.name,
            func.min(cls.price).label("min_price"),
            func.max(cls.price).label("max_price")
        ).group_by(
            cls.name
        ).order_by(
            func.min(cls.price).desc()
        ).all()

        return [
            {
                "name": row.name,
                "min_price": row.min_price,
                "max_price": row.max_price
            }
            for row in rows
        ]
