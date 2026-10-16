"""Seeder for station role lookup data."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.station_role import StationRoleModel
from seeders.base import Seeder


class StationRolesSeeder(Seeder):
    roles = (
        ("Manager", "Responsible for overall station management and operations."),
        ("Cashier", "Handles cash transactions and customer payments."),
        ("Fuel Attendant", "Assists customers with fueling their vehicles and maintaining the fuel pumps."),
        ("Maintenance Staff", "Responsible for maintaining and repairing station equipment and facilities."),
        ("Security Personnel", "Ensures the safety and security of the station premises and customers."),
    )

    def run(self, session: Session) -> None:
        existing_names = set(
            session.scalars(select(StationRoleModel.name)).all()
        )
        session.add_all(
            StationRoleModel(name=name, description=description)
            for name, description in self.roles
            if name not in existing_names
        )
        session.flush()
