from datetime import datetime

from sqlalchemy import String, Float, DateTime, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


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
        String(100),
        nullable=False
    )

    price: Mapped[float] = mapped_column(
        Float,
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
