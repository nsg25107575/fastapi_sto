from datetime import datetime
from math import radians
from typing import Self
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from sqlalchemy import String, Boolean, DateTime, Index, UniqueConstraint, text, select, event, func, case, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, Session, with_loader_criteria, selectinload, relationship
from sqlalchemy.sql.sqltypes import Numeric, Integer

from config import Config
from database.engine import Base
from database.pagination import paginate
from models.mixin import SoftDeleteMixin

if TYPE_CHECKING:
    from models.station_service import StationServiceModel
    from models.user import UserModel


class StationModel(Base, SoftDeleteMixin):
    """
    # Bypassing the global filter using execution_options
    all_stations = session.scalars(
        select(StationModel).execution_options(include_deleted=True)
    ).all()
    # Record restoration (Restore)
    station.deleted_at = None
    station.commit()
    """
    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer(), ForeignKey("users.id"), nullable=False)
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

    __table_args__ = (
        UniqueConstraint("name", "address", name="uq_station_name_per_address"),
        Index("idx_station_address", "address"),
        Index("idx_station_latitude_longitude", "latitude", "longitude"),
        # Full-text index for fast search by title
        Index("idx_station_name_fulltext", "name", mariadb_prefix="FULLTEXT")
    )

    # Connection to the service model
    services: Mapped[list["StationServiceModel"]] = relationship(
        "StationServiceModel",
        back_populates="station",
    )

    # Connection to the user model
    user: Mapped["UserModel"] = relationship(
        "UserModel",
    )

    @classmethod
    def search_stations_by_name(cls, session: Session, search_query: str, limit: int = 20):
        """
        Fast full-text search for stations by name.
        Returns only active service stations that have not been soft-deleted.
        """
        if not search_query or len(search_query.strip()) < 3:
            return []

        # Constructing a query for Boolean Mode.
        # Adding '*' allows searching by the beginning of a word (e.g., 'Auto*' will find 'Autoservice', 'Autotech').
        formatted_query = f"{search_query.strip()}*"

        # Constructing the SQL expression MATCH(name) AGAINST(:query IN BOOLEAN MODE)
        match_expr = func.match(cls.name).against(formatted_query, text("IN BOOLEAN MODE"))

        stmt = (
            select(cls)
            .where(
                match_expr,
                cls.active.is_(True)
            )
            .limit(limit)
        )

        return session.scalars(stmt).all()

    @classmethod
    def create_station(cls, session: Session, user_id: int, name: str, address: str) -> Self:
        """
        Create a new station and add it to the current database session.
        """
        station = cls(user_id=user_id, name=name, address=address)
        session.add(station)
        session.flush()  # Generates an ID without saving (transaction management remains in the router)

        return station

    @classmethod
    def read_station(cls, session: Session, station_id: int) -> Self | None:
        """
        Find the station by its ID. Returns None if the station does not exist.
        """
        stmt = select(cls).where(cls.id == station_id)
        return session.scalars(stmt).first()

    @classmethod
    def read_stations(cls, session: Session, offset: int = 0, limit: int = 20) -> tuple[list["StationModel"], int]:
        """
        Returns a page of stations and the total count, using offset/limit pagination.
        """
        stmt = select(cls)
        return paginate(session, stmt, offset, limit)

    @classmethod
    def read_nearest_stations(
            cls, session: Session, lat: float, lng: float,
            limit: int = Config.app_nearest_stations_limit
    ) -> list[Self]:
        """
        Returns the nearest active stations along with their services,
        calculating the distance on the database side.
        """
        # 1. Convert user coordinates to radians for SQL
        rad_lat = radians(lat)
        rad_lng = radians(lng)
        earth_radius = 6371

        # Calculate the argument of the cosines
        cos_expr = (
                func.cos(rad_lat) * func.cos(func.radians(cls.latitude)) *
                func.cos(func.radians(cls.longitude) - rad_lng) +
                func.sin(rad_lat) * func.sin(func.radians(cls.latitude))
        )
        # Protection against NaN: if the value exceeds 1.0 due to an error, force it to 1.0.
        # If it is less than -1.0, set it to -1.0
        safe_cos_expr = case(
            (cos_expr > 1.0, 1.0),
            (cos_expr < -1.0, -1.0),
            else_=cos_expr
        )

        # 2. Haversine / Cosine formula with safeguards
        distance_expr = (earth_radius * func.acos(safe_cos_expr)).label("distance_km")

        # 3. Database query (adding filters for active and non-deleted stations)
        stmt = (
            select(cls, distance_expr)
            .where(
                cls.latitude.is_not(None),
                cls.longitude.is_not(None),
                cls.active.is_(True)  # return only active ones
            )
            .options(selectinload(cls.services))
            # sort by the alias or by the expression itself for reliability
            .order_by(text("distance_km"))
            .limit(limit)
        )

        # Fulfilling the request.
        results = session.execute(stmt).all()

        # 4. Formulating the final result
        final_result = []
        for station, distance_km in results:
            final_result.append({
                "id": station.id,
                "name": station.name,
                "address": station.address,
                "latitude": station.latitude,
                "longitude": station.longitude,
                "distance_km": round(distance_km, 2),
                # Sorting services by price
                "services": [
                    {"name": srv.name, "price": srv.price}
                    for srv in sorted(station.services, key=lambda s: s.price if s.price is not None else 0.0)
                ]
            })

        return final_result

    @classmethod
    def update_station(cls, session: Session, station_id: int, **kwargs) -> Self | None:
        """
        Update the station with the given ID using the provided fields.
        """
        station = cls.read_station(session, station_id)

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
        Delete (by soft delete) a station by its ID.
        """
        station = cls.read_station(session, station_id)

        if station is None:
            return None

        tz = ZoneInfo(Config.app_timezone)
        station.deleted_at = datetime.now(tz)
        session.flush()

        return station_id

    @classmethod
    def restore_station(cls, session: Session, station_id: int) -> Self | None:
        """
        Restore the station with the given ID.
        """
        # Must bypass the global soft-delete filter — otherwise a
        # soft-deleted station (deleted_at IS NOT NULL) is invisible to
        # read_station() and can never be found to restore.
        stmt = select(cls).where(cls.id == station_id).execution_options(include_deleted=True)
        station = session.scalars(stmt).first()

        if station is not None:
            station.deleted_at = None
            session.flush()
        return station


# Global Request Interceptor (Event Listener)
@event.listens_for(Session, "do_orm_execute")
def _add_soft_delete_filter(execute_state):
    # Allows disabling the filter using .execution_options(include_deleted=True)
    if execute_state.execution_options.get("include_deleted", False):
        return
    # Filtering SELECT queries: showing only those where deleted_at IS NULL
    if execute_state.is_select:
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                SoftDeleteMixin,
                lambda cls: cls.deleted_at.is_(None),
                include_aliases=True,
                propagate_to_loaders=True
            )
        )
