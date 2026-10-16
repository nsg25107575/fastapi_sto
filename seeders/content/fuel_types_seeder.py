"""Seeder for vehicle fuel type lookup data."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.vehicle import FuelTypeModel
from seeders.base import Seeder


class FuelTypesSeeder(Seeder):
    fuel_types = ("Petrol", "Diesel", "Electric", "Hybrid", "LPG", "CNG")

    def run(self, session: Session) -> None:
        existing_names = set(session.scalars(select(FuelTypeModel.name)).all())
        session.add_all(
            FuelTypeModel(name=name)
            for name in self.fuel_types
            if name not in existing_names
        )
        session.flush()
