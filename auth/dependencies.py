from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.config import manager
from config import Config
from database.engine import engine
from models.token import TokenModel
from models.user import UserModel


# NOTE: `user_loader` is a factory that returns the actual decorator — it
# MUST be called (`@manager.user_loader()`), otherwise `load_user` is
# passed as a positional arg to the factory and `_user_callback` is never
# set, breaking all authentication with "Missing user_loader callback".
@manager.user_loader()
def load_user(email: str):
    stmt = (
        select(UserModel)
        .join(TokenModel, TokenModel.user_id == UserModel.id)
        .where(
            UserModel.email == email,
            TokenModel.expires_at > Config.get_current_time()
        )
    )
    # session.scalars(...).first() returns the model object directly or None.
    with Session(engine) as session:
        user = session.scalars(stmt).first()

        return user


def get_current_user(user: UserModel = Depends(manager)) -> UserModel:
    """
    The manager has already called `load_user`, verified the token in the database, and returned the user.
    If the token is invalid, the manager itself will throw a 401 Unauthorized error.
    """

    return user
