from abc import ABC, abstractmethod

from sqlalchemy.orm import Session


class Seeder(ABC):
    @abstractmethod
    def run(self, session: Session) -> None:
        """Insert or update this seeder's data using the provided session."""
