from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

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

from models.station_service import StationServiceModel


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
    def read_nearest_stations(
            session,
            lat: float,
            lng: float,
            limit: int = 5
    ):
        stations = session.query(
            StationModel
        ).filter(
            StationModel.latitude.is_not(None),
            StationModel.longitude.is_not(None)
        ).all()

        earth_radius = 6371

        result = []

        for station in stations:
            station_lat = float(station.latitude)
            station_lng = float(station.longitude)

            lat1 = radians(lat)
            lng1 = radians(lng)
            lat2 = radians(station_lat)
            lng2 = radians(station_lng)

            dlat = lat2 - lat1
            dlng = lng2 - lng1

            a = (
                    sin(dlat / 2) ** 2
                    + cos(lat1)
                    * cos(lat2)
                    * sin(dlng / 2) ** 2
            )

            c = 2 * atan2(sqrt(a), sqrt(1 - a))

            distance = earth_radius * c

            services = session.query(
                StationServiceModel.name
            ).filter(
                StationServiceModel.station_id == station.id
            ).all()

            result.append(
                {
                    "id": station.id,
                    "name": station.name,
                    "address": station.address,
                    "latitude": station.latitude,
                    "longitude": station.longitude,
                    "distance_km": round(distance, 2),
                    "services": [
                        service.name
                        for service in services
                    ],
                }
            )

        result.sort(key=lambda station: station["distance_km"])

        return result[:limit]

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
