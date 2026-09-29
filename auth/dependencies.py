from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.config import manager
from config import Config
from database.engine import get_session
from exceptions import TokenExpiredException
from models.token import TokenModel
from models.user import UserModel


def get_current_user(email: str = Depends(manager), session: Session = Depends(get_session)) -> UserModel:
    """
    The manager will independently extract the "station" cookie, decode it, and return the email in the `sub` field.
    """
    # Search for the user in the database using a single request session
    user = session.query(UserModel).filter(UserModel.email == email).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Additional check: is this token active in database (App timezone)
    current_time = datetime.now(ZoneInfo(Config.app_timezone))

    token_active = session.query(TokenModel).filter(
        TokenModel.user_id == user.id,
        TokenModel.expires_at > current_time
    ).first()

    if not token_active:
        raise TokenExpiredException

    return user
