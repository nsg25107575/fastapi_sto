from sqlalchemy import String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, Session
from sqlalchemy.sql.schema import Index, UniqueConstraint
from sqlalchemy.exc import IntegrityError

Base = declarative_base()


class StationModel(Base):
    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(200), nullable=False)
    lng: Mapped[float] = mapped_column(nullable=True)
    lat: Mapped[float] = mapped_column(nullable=True)

    __table_args__ = (
        Index("idx_station_name_address", "name", "address", unique=True),
        Index("idx_station_lng_lat", "lng", "lat", unique=False),
        UniqueConstraint("name", "address", name="uq_station_name_per_address"),
    )

    @staticmethod
    def create_station(
            session: Session,
            name: str,
            address: str
    ):
        station = StationModel(
            name=name,
            address=address
        )

        try:
            session.add(station)
            session.commit()
            session.refresh(station)

            return station

        except IntegrityError:
            session.rollback()
            raise

    @staticmethod
    def read_station(
            session: Session,
            station_id: int
    ):
        return session.get(StationModel, station_id)

    @staticmethod
    def read_stations(
            session: Session
    ):
        return session.query(StationModel).all()

    @staticmethod
    def update_station(
            # connection bd
            session: Session,
            # Which station are we looking for?
            station_id: int,
            name: str | None = None,
            address: str | None = None
    ):
        station = session.get(StationModel, station_id)

        if station is None:
            return None

        if name is not None:
            station.name = name

        if address is not None:
            station.address = address

        session.commit()
        session.refresh(station)

        return station

    @staticmethod
    def delete_station(
            # connection bd
            session: Session,
            # Which station are we looking for?
            station_id: int
    ):
        station = session.get(StationModel, station_id)

        if station is None:
            return None

        try:
            session.delete(station)
            session.commit()

            return station_id
        # If an error occurs during deletion, the transaction is rolled back.
        except Exception:
            session.rollback()
            raise
