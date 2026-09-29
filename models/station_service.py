from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Index, text, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from database.engine import Base


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
