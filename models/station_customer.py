from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class StationCustomerModel(Base):
    __tablename__ = "station_customers"

    id: Mapped[int] = mapped_column(
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

    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True
    )

    problem_description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False
    )

    __table_args__ = (
        Index(
            "idx_station_customer_phone",
            "phone",
            unique=True
        ),
    )
