import enum
from datetime import datetime
from math import radians
from typing import Self, Optional
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from sqlalchemy import String, Boolean, DateTime, Index, UniqueConstraint, text, select, func, case, ForeignKey, \
    Enum
from sqlalchemy.orm import Mapped, mapped_column, Session, selectinload, relationship
from sqlalchemy.sql.sqltypes import Numeric, Integer

from config import Config
from database.engine import Base
from database.pagination import paginate
from models.mixin import SoftDeleteMixin

if TYPE_CHECKING:
    from models.station_service import StationServiceModel
    from models.user import UserModel


class ModerationStatus(str, enum.Enum):
    """Enum for station moderation statuses."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


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

    moderation_status: Mapped[ModerationStatus] = mapped_column(
        Enum(ModerationStatus, native_enum=False, length=20,
             values_callable=lambda enum_cls: [member.value for member in enum_cls]),
        nullable=False,
        default=ModerationStatus.PENDING,
        server_default=text("'pending'"),
    )

    rejection_reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )

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
        Returns only active, approved service stations that have not been soft-deleted.
        """
        if not search_query or len(search_query.strip()) < 3:
            return []

        # Constructing a query for Boolean Mode.
        formatted_query = f"{search_query.strip()}*"

        # Constructing the SQL expression MATCH(name) AGAINST(:query IN BOOLEAN MODE)
        match_expr = func.match(cls.name).against(formatted_query, text("IN BOOLEAN MODE"))

        stmt = (
            select(cls)
            .where(
                match_expr,
                cls.active.is_(True),
                cls.moderation_status == ModerationStatus.APPROVED  # Додано фільтрацію
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
    ) -> list[dict]:
        """
        Returns the nearest active approved stations along with their services and
        on-the-fly aggregated review rating/count.
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

        # Protection against floating-point values outside [-1, 1]
        safe_cos_expr = case(
            (cos_expr > 1.0, 1.0),
            (cos_expr < -1.0, -1.0),
            else_=cos_expr
        )

        # 2. Calculate distance
        distance_expr = (
                earth_radius * func.acos(safe_cos_expr)
        ).label("distance_km")

        # 3. Aggregate reviews separately.
        from models.review import ReviewModel

        reviews_aggregation = (
            select(
                ReviewModel.station_id.label("station_id"),
                func.avg(ReviewModel.rating).label("rating"),
                func.count(ReviewModel.station_id).label("reviews_count"),
            )
            .subquery()
        )

        # 4. Get nearest stations and attach aggregated review data.
        stmt = (
            select(
                cls,
                distance_expr,
                reviews_aggregation.c.rating,
                reviews_aggregation.c.reviews_count,
            )
            .outerjoin(
                reviews_aggregation,
                reviews_aggregation.c.station_id == cls.id
            )
            .where(
                cls.latitude.is_not(None),
                cls.longitude.is_not(None),
                cls.active.is_(True),
                cls.moderation_status == ModerationStatus.APPROVED  # Додано перевірку статусу схвалення
            )
            .options(selectinload(cls.services))
            .order_by(text("distance_km"))
            .limit(limit)
        )

        # 5. Execute query
        results = session.execute(stmt).all()

        # 6. Build response
        final_result = []

        for station, distance_km, rating, reviews_count in results:
            final_result.append({
                "id": station.id,
                "name": station.name,
                "address": station.address,
                "latitude": station.latitude,
                "longitude": station.longitude,
                "distance_km": round(distance_km, 2),
                "rating": float(rating) if rating is not None else None,
                "reviews_count": reviews_count or 0,
                "services": [
                    {
                        "name": srv.name,
                        "price": srv.price
                    }
                    for srv in sorted(
                        station.services,
                        key=lambda s: s.price if s.price is not None else 0.0
                    )
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
        """Restore the station with the given ID."""
        stmt = (
            select(cls)
            .where(cls.id == station_id)
            .execution_options(include_deleted=True)
        )
        station = session.scalars(stmt).first()

        if station is not None:
            station.deleted_at = None
            session.flush()

        return station
