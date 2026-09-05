from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class StationUserModel(Base):
    __tablename__ = "station_users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    station_id: Mapped[int] = mapped_column(
        ForeignKey("stations.id"),
        nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    role_id: Mapped[int] = mapped_column(
        Integer,
        server_default="1",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default="CURRENT_TIMESTAMP",
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default="CURRENT_TIMESTAMP",
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "station_id",
            "user_id"
        ),
    )
