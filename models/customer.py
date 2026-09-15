from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import Numeric

from database import Base


class CustomerModel(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    ip: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
    )

    device_hash: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
    )

    lat: Mapped[float] = mapped_column(
        Numeric(precision=16, scale=14),
        nullable=False,
    )

    lng: Mapped[float] = mapped_column(
        Numeric(precision=16, scale=14),
        nullable=False,
    )

    public_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )
