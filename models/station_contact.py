from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class StationContactModel(Base):
    __tablename__ = "station_contacts"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    station_id: Mapped[int] = mapped_column(
        ForeignKey("stations.id"),
        nullable=False
    )

    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    value: Mapped[str] = mapped_column(
        String(255),
        nullable=False
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
            "idx_station_contact_type",
            "type"
        ),
        Index(
            "idx_station_contact_value",
            "value"
        ),
    )