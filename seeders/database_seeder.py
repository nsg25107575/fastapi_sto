from sqlalchemy.orm import Session

from seeders.base import Seeder
from seeders.registry import discover_seeders, resolve_seeder_order


class DatabaseSeeder(Seeder):
    def run(self, session: Session) -> None:
        seeders = discover_seeders()
        for seeder_class in resolve_seeder_order(seeders):
            seeder_class().run(session)
