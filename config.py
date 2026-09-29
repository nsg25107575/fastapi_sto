import dataclasses as dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass.dataclass
class Config:
    # App configuration
    app_env: str = os.getenv("APP_ENV", "development")
    app_timezone: str = os.getenv("APP_TIMEZONE", "Europe/Kyiv")
    # App configuration for search
    app_nearest_stations_limit: int = int(os.getenv("APP_NEAREST_STATIONS_LIMIT", 10))

    # DB configuration
    db_url: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    # JWT configuration
    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY",
        "OFXiUpIEzMYniAwbvAKBW1TBPRopiVAY0FSjJUAZzK0sEbZy7mwuTCSkU8gLUuR49lX9ibKaBJ5HyVJKKQj867YPssV8N67L9PmBjCexMUXS3y3EVFTn7jSjsSwto95mhkaImzlKNekAAi6vLgDU79fQszEZaoOF4nzrrbl4PnqpFlBAYyEylGTWv9rK6RLpzNLb3iyc8zEB9sqkgXtS9UK7RJRCQxh5pjxfdJELc1MquYeS5HbfTdTJaBL5t4D2"
    )
    jwt_algorithm: str = "HS256"
    jwt_expires_in: int = int(os.getenv("JWT_EXPIRES_IN", 3600))

    # Cookies configuration
    cookie_secret: str = os.getenv("COOKIES_SECRET_KEY", "")
    cookie_secure: bool = bool(os.getenv("COOKIES_SECURE", False))  # TODO: сhange to True for HTTPS in production
