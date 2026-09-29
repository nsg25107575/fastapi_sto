from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

from sqlalchemy import String, Boolean, DateTime, Index, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, Session
from sqlalchemy.sql.sqltypes import Numeric

from config import Config
from database.engine import Base


class StationModel(Base):
    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(200), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"))

    latitude: Mapped[float | None] = mapped_column(Numeric(precision=16, scale=14), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(precision=16, scale=14), nullable=True)

    # App timezone support
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("name", "address", name="uq_station_name_per_address"),
        Index("idx_station_name", "name"),
        Index("idx_station_address", "address"),
        Index("idx_station_longitude_latitude", "longitude", "latitude"),
    )

    @classmethod
    def create_station(cls, session: Session, name: str, address: str) -> "StationModel":
        """
        Create a new station and add it to the current database session.
        """
        station = cls(name=name, address=address)
        session.add(station)
        session.flush()  # Generates an ID without saving (transaction management remains in the router)
        return station

    @classmethod
    def read_station(cls, session: Session, station_id: int) -> "StationModel | None":
        """
        Find the station by its ID. Returns None if the station does not exist.
        """
        return session.get(cls, station_id)

    @classmethod
    def read_stations(cls, session: Session):
        """
        Returns all stations from the database.
        """
        return session.query(cls).all()

    @classmethod
    def read_nearest_stations(
            cls, session: Session, lat: float, lng: float,
            limit: int = Config.app_nearest_stations_limit
    ):
        """
        Returns the nearest active stations to the specified coordinates.
        """
        # Retrieving all stations
        stations = session.query(cls).filter(
            cls.latitude.is_not(None),
            cls.longitude.is_not(None)
        ).all()

        if not stations:
            return []

        # N+1 Optimization: Retrieve ALL services for the found stations in a SINGLE request
        station_ids = [s.id for s in stations]
        services_query = text("""SELECT station_id, name, price
                                 FROM station_services
                                 WHERE station_id IN :ids
                                 ORDER BY price DESC""")
        services_result = session.execute(services_query, {"ids": tuple(station_ids)}).mappings().all()

        # Group services by station ID into a standard dictionary
        services_by_station = {}
        for srv in services_result:
            st_id = srv["station_id"]
            if st_id not in services_by_station:
                services_by_station[st_id] = []
            services_by_station[st_id].append({"name": srv["name"], "price": srv["price"]})

        earth_radius = 6371
        result = []

        # Calculating distances (without database queries inside the loop)
        for station in stations:
            station_lat = float(station.latitude)
            station_lng = float(station.longitude)

            lat1, lng1 = radians(lat), radians(lng)
            lat2, lng2 = radians(station_lat), radians(station_lng)

            dlat = lat2 - lat1
            dlng = lng2 - lng1

            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            distance = earth_radius * c

            result.append({
                "id": station.id,
                "name": station.name,
                "address": station.address,
                "latitude": station.latitude,
                "longitude": station.longitude,
                "distance_km": round(distance, 2),
                # Take the prepared data from our grouped dictionary (an empty list if there are no services)
                "services": services_by_station.get(station.id, []),
            })

        result.sort(key=lambda x: x["distance_km"])
        return result[:limit]

    @classmethod
    def update_station(cls, session: Session, station_id: int, **kwargs) -> "StationModel | None":
        """
        Update the station with the given ID using the provided fields.
        """
        station = session.get(cls, station_id)
        if station is None:
            return None

        for key, value in kwargs.items():
            if value is not None:
                setattr(station, key, value)

        session.flush()
        return station

    @classmethod
    def delete_station(cls, session: Session, station_id: int) -> int | None:
        """
        Delete a station by its ID.
        """
        station = session.get(cls, station_id)
        if station is None:
            return None

        session.delete(station)
        session.flush()
        return station_id
