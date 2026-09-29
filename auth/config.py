from datetime import timedelta, datetime
from zoneinfo import ZoneInfo

from fastapi_login import LoginManager
from sqlalchemy.orm import Session

from config import Config
from database.engine import engine
from models.token import TokenModel
from models.user import UserModel

# Cookie lifetime in days
MAX_COOKIE_AGE_IN_DAYS = 7

# Set the validity period of the JWT token itself to 7 days.
manager = LoginManager(
    secret=Config.cookie_secret,  # The secret key (solt) for generate the access token & cookie value
    token_url="/auth/sign-in",
    default_expiry=timedelta(days=MAX_COOKIE_AGE_IN_DAYS),  # The JWT cookie will expire in 7 days.
    use_cookie=True,
    cookie_name="station",
)

# General config for secure cookies
COOKIE_PARAMS = {
    "key": manager.cookie_name,  # "station"
    "httponly": True,
    "samesite": "lax",
    "secure": Config.cookie_secure,
}


@manager.user_loader
def load_user(email: str):
    with Session(engine) as session:
        user = session.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            return None

        current_time = datetime.now(ZoneInfo(Config.app_timezone))

        # Check whether the token for this user is active.
        token_exists = session.query(TokenModel).filter(
            TokenModel.user_id == user.id,
            TokenModel.expires_at > current_time
        ).first()

        if not token_exists:
            return None

        return user
