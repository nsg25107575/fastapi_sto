from sqlalchemy import select

from models.station_role import StationRoleModel
from models.vehicle import FuelTypeModel
from seeders.content.fuel_types_seeder import FuelTypesSeeder
from seeders.content.station_roles_seeder import StationRolesSeeder
from seeders.database_seeder import DatabaseSeeder


def test_database_seeder_inserts_lookup_data_and_is_idempotent(db_session):
    seeder = DatabaseSeeder()

    seeder.run(db_session)
    seeder.run(db_session)

    role_names = set(db_session.scalars(select(StationRoleModel.name)).all())
    fuel_type_names = set(db_session.scalars(select(FuelTypeModel.name)).all())

    assert role_names == {name for name, _description in StationRolesSeeder.roles}
    assert fuel_type_names == set(FuelTypesSeeder.fuel_types)
