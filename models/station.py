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
from sqlalchemy.sql.sqltypes import Numeric

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
        Numeric(precision=16, scale=14),
        nullable=True
    )

    longitude: Mapped[float | None] = mapped_column(
        Numeric(precision=16, scale=14),
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

    @staticmethod
    def create_station(
            session,
            name: str,
            address: str
    ):
        station = StationModel(
            name=name,
            address=address
        )

        session.add(station)
        session.commit()
        session.refresh(station)

        return station

    @staticmethod
    def read_station(
            session,
            station_id: int
    ):
        return session.get(
            StationModel,
            station_id
        )

    @staticmethod
    def read_stations(
            session
    ):
        return session.query(
            StationModel
        ).all()

    @staticmethod
    def update_station(
            session,
            station_id: int,
            name: str | None = None,
            address: str | None = None,
            active: bool | None = None
    ):
        station = session.get(
            StationModel,
            station_id
        )

        if station is None:
            return None

        if name is not None:
            station.name = name

        if address is not None:
            station.address = address

        if active is not None:
            station.active = active

        session.commit()
        session.refresh(station)

        return station

    @staticmethod
    def delete_station(
            session,
            station_id: int
    ):
        station = session.get(
            StationModel,
            station_id
        )

        if station is None:
            return None

        session.delete(station)
        session.commit()

        return station_id
