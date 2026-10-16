import pytest
from sqlalchemy import select

from models.station import StationModel
from models.station_role import StationRoleModel
from models.vehicle import FuelTypeModel
from seeders.base import Seeder
from seeders.content.fake_stations_seeder import FakeStationsSeeder
from seeders.content.fake_users_seeder import FakeUsersSeeder
from seeders.content.fuel_types_seeder import FuelTypesSeeder
from seeders.content.station_roles_seeder import StationRolesSeeder
from seeders.database_seeder import DatabaseSeeder
from seeders.registry import resolve_seeder_order


def test_lookup_seeders_insert_data_and_are_idempotent(db_session):
    seeders = {
        "fuel_types": FuelTypesSeeder,
        "station_roles": StationRolesSeeder,
    }
    order = resolve_seeder_order(seeders)
    for seeder_class in order:
        seeder_class().run(db_session)
    for seeder_class in order:
        seeder_class().run(db_session)

    role_names = set(db_session.scalars(select(StationRoleModel.name)).all())
    fuel_type_names = set(db_session.scalars(select(FuelTypeModel.name)).all())

    assert role_names == {name for name, _description in StationRolesSeeder.roles}
    assert fuel_type_names == set(FuelTypesSeeder.fuel_types)


def test_fake_stations_seeder_adds_station_rows_and_is_idempotent(db_session):
    FakeUsersSeeder().run(db_session)
    seeder = FakeStationsSeeder()

    seeder.run(db_session)
    seeder.run(db_session)

    stations = db_session.scalars(select(StationModel)).all()
    assert len(stations) == 10
    assert {station.address for station in stations} == {
        f"Fake address {number}" for number in range(1, 11)
    }


def test_database_seeder_runs_all_seeders_in_dependency_order(db_session):
    seeder = DatabaseSeeder()
    seeder.run(db_session)
    seeder.run(db_session)

    stations = db_session.scalars(select(StationModel)).all()
    assert len(stations) == 10


def test_resolve_seeder_order_runs_dependencies_first_even_for_single_target():
    class PrerequisiteSeeder(Seeder):
        def run(self, session):
            pass

    class DependentSeeder(Seeder):
        depends_on = (PrerequisiteSeeder,)

        def run(self, session):
            pass

    seeders = {
        "dependent": DependentSeeder,
        "prerequisite": PrerequisiteSeeder,
    }

    assert resolve_seeder_order(seeders, (DependentSeeder,)) == [
        PrerequisiteSeeder,
        DependentSeeder,
    ]


def test_resolve_seeder_order_rejects_circular_dependencies():
    class FirstSeeder(Seeder):
        def run(self, session):
            pass

    class SecondSeeder(Seeder):
        depends_on = (FirstSeeder,)

        def run(self, session):
            pass

    FirstSeeder.depends_on = (SecondSeeder,)

    with pytest.raises(ValueError, match="Circular seeder dependency"):
        resolve_seeder_order(
            {"first": FirstSeeder, "second": SecondSeeder},
            (FirstSeeder,),
        )
