from fastapi_login import LoginManager

from config import Config

# Set the validity period of the JWT token itself to 7 days.
manager = LoginManager(
    secret=Config.jwt_secret_key,
    token_url="/auth/sign-in",
    default_expiry=Config.get_cookie_lifetime(),  # The JWT cookie will expire in 7 days.
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
