from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from sqlalchemy.orm import Session


class Seeder(ABC):
    depends_on: ClassVar[tuple[type[Seeder], ...]] = ()

    @abstractmethod
    def run(self, session: Session) -> None:
        """Insert or update this seeder's data using the provided session."""
