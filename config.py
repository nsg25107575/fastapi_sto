import dataclasses as dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass.dataclass
class Config:
    """
    Configuration class for the application.
    This class is responsible for loading and managing application settings.
    """

    db_url: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
