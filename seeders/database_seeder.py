from sqlalchemy.orm import Session

from seeders.base import Seeder
from seeders.registry import discover_seeders


class DatabaseSeeder(Seeder):
    def run(self, session: Session) -> None:
        for _name, seeder_class in discover_seeders().items():
            seeder_class().run(session)
