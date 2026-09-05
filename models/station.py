from datetime import datetime

from sqlalchemy import (
    String,
    Boolean,
    Float,
    DateTime,
    Index,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column


from database import Base


class StationModel(Base):
    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    address: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("1")
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    longitude: Mapped[float | None] = mapped_column(
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
        server_default=text("CURRENT_TIMESTAMP")
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "name",
            "address",
            name="uq_station_name_per_address"
        ),

        Index(
            "idx_station_name",
            "name"
        ),

        Index(
            "idx_station_address",
            "address"
        ),

        Index(
            "idx_station_longitude_latitude",
            "longitude",
            "latitude"
        ),
    )
