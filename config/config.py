import dataclasses as dataclass
import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


def _build_db_url() -> str:
    """
    Builds the SQLAlchemy database URL. Prefers an explicit DATABASE_URL
    (e.g. set in docker-compose.yml for the containerized setup); falls
    back to assembling it from the discrete DB_* variables defined in
    .env (used for local/non-Docker runs), and finally to a local sqlite
    file if nothing is configured.
    """
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url

    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME")

    if db_user and db_password and db_name:
        return (
            f"mariadb+mariadbconnector://{db_user}:{db_password}"
            f"@{db_host}:{db_port}/{db_name}"
        )

    return "sqlite:///./test.db"


@dataclass.dataclass
class Config:
    # App configuration
    app_env: str = os.getenv("APP_ENV", "development")
    app_timezone: str = os.getenv("APP_TIMEZONE", "Europe/Kyiv")
    # Default locale for i18n, used when no other locale is specified or detected
    app_default_locale: str = os.getenv("APP_DEFAULT_LOCALE", "en")
    # Supported locales for i18n
    app_sup_locales: tuple[dict, ...] = tuple(json.loads(
        os.getenv("APP_SUPPORTED_LOCALES", '[{"abbr":"en","name":"English"}]')
    ))
    # App configuration for search
    app_nearest_stations_limit: int = int(os.getenv("APP_NEAREST_STATION_LIMIT", 10))

    # Geocoding (address -> lat/lng) configuration, used when creating a
    # station so its coordinates don't have to be set manually. Defaults
    # to the free OpenStreetMap Nominatim endpoint; a descriptive
    # User-Agent is required by Nominatim's usage policy.
    geocoding_base_url: str = os.getenv("GEOCODING_BASE_URL", "https://nominatim.openstreetmap.org/search")
    geocoding_user_agent: str = os.getenv("GEOCODING_USER_AGENT", "kws-station-api/1.0")
    geocoding_timeout: float = float(os.getenv("GEOCODING_TIMEOUT", 5))

    # Email / SMTP configuration
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", 587))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", "")
    smtp_from_name: str = os.getenv("SMTP_FROM_NAME", "KWS Station")
    smtp_security: str = os.getenv("SMTP_SECURITY", "starttls").strip().lower()
    smtp_timeout: float = float(os.getenv("SMTP_TIMEOUT", 10))
    # DB configuration
    db_url: str = _build_db_url()

    # JWT configuration
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "supersecretkey")  # TODO: change to a secure key in production
    jwt_algorithm: str = "HS256"
    jwt_expires_in: int = int(os.getenv("JWT_EXPIRES_IN", 3600))

    # Cookies configuration
    cookie_secret: str = os.getenv("COOKIES_SECRET_KEY", "supersecretkey")  # TODO: change to a secure key in production
    cookie_secure: bool = bool(os.getenv("COOKIES_SECURE", False))  # TODO: change to True for HTTPS in production
    max_cookie_lifetime_in_days: int = int(os.getenv("MAX_COOKIE_AGE_IN_DAYS", 7))

    @classmethod
    def get_current_time(cls) -> datetime:
        """
        Returns the current time in the config time zone.
        """
        return datetime.now(ZoneInfo(cls.app_timezone))

    @classmethod
    def get_cookie_lifetime(cls) -> timedelta:
        """
        Returns the cookie lifetime.
        """
        return timedelta(days=cls.max_cookie_lifetime_in_days)
