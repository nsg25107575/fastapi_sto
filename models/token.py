from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, Session

from config import Config
from database.engine import Base


def get_default_expiry():
    """
    Use timezone-aware UTC
    """
    tz = ZoneInfo(Config.app_timezone)
    return datetime.now(tz) + timedelta(days=7)


class TokenModel(Base):
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(512), nullable=False)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=get_default_expiry
    )

    @classmethod
    def save_token(cls, user_id: int, access_token: str, session: Session) -> str:
        new_token = cls(
            user_id=user_id,
            token=access_token
        )
        session.add(new_token)
        session.flush()
        return new_token.token
