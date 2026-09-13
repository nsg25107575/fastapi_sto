from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

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
        String(20),
        nullable=False,
    )

    lat: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    lng: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
