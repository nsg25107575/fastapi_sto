from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, select
from sqlalchemy.orm import Mapped, mapped_column, Session, relationship

from auth.password import get_password_hash
from database.engine import Base

if TYPE_CHECKING:
    from models.station import StationModel

class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Use `DateTime(timezone=True)` to synchronize with the application's server time.
    email_verified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    second_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    password: Mapped[str] = mapped_column(String(256), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Connection to the service model
    stations: Mapped[list["StationModel"]] = relationship(
        "StationModel",
        back_populates="user",
    )

    @classmethod
    def get_user_by_email(cls, email: str, session: Session) -> "UserModel | None":
        """
        Searches for a user by email within the provided session.
        :param email: Email of the user
        :param session: Session
        """
        stmt = select(cls).where(cls.email == email)
        return session.scalars(stmt).first()

    @classmethod
    def create_user(
            cls,
            email: str,
            password: str,
            first_name: str | None,
            second_name: str | None,
            last_name: str | None,
            session: Session
    ) -> "UserModel":
        """
        Creates a user object and adds it to the current session transaction.
        :param email: Email of the user
        :param password: Password of the user
        :param first_name: First name of the user
        :param second_name: Second name of the user
        :param last_name: Last name of the user
        :param session: Session
        """
        new_user = cls(
            email=email,
            password=get_password_hash(password),
            first_name=first_name,
            second_name=second_name,
            last_name=last_name
        )
        session.add(new_user)
        session.flush()  # Generates an ID for the user in the database but doesn't commit the transaction.
        return new_user
