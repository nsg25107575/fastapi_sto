import dataclasses as dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass.dataclass
class Config:
    db_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./test.db"
    )

    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY",
        ""
    )

    jwt_algorithm: str = "HS256"

    token_expiration_minutes: int = 30
