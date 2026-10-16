"""Seeder for stations fake data."""
import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import StationModel, UserModel
from models.station import ModerationStatus
from seeders.base import Seeder
from seeders.content.fake_users_seeder import FakeUsersSeeder

USER_LATITUDE = 48.49689099250345
USER_LONGITUDE = 32.23869921769066

FAKE_STATIONS_COUNT = 10
COORDINATE_OFFSET = 5


class FakeStationsSeeder(Seeder):
    depends_on = (FakeUsersSeeder,)

    @staticmethod
    def fill_stations(session: Session) -> list[tuple[int, str, str, float, float]]:
        user_id = session.scalars(select(UserModel.id).where(UserModel.email == "fake_user@example.com")).one()
        stations = []
        for i in range(1, FAKE_STATIONS_COUNT + 1):
            latitude = USER_LATITUDE + random.uniform(
                -COORDINATE_OFFSET,
                COORDINATE_OFFSET,
            )

            longitude = USER_LONGITUDE + random.uniform(
                -COORDINATE_OFFSET,
                COORDINATE_OFFSET,
            )

            stations.append(
                (user_id, f"Fake STO {i}", f"Fake address {i}", ModerationStatus.APPROVED, latitude, longitude)
            )
        return stations

    def run(self, session: Session) -> None:
        stations = FakeStationsSeeder.fill_stations(session)

        existing_stations = set(
            session.scalars(select(StationModel.address)).all()
        )
        session.add_all(
            StationModel(
                user_id=user_id,
                name=name,
                address=address,
                moderation_status=m_status,
                latitude=latitude,
                longitude=longitude,
            )
            for user_id, name, address, m_status, latitude, longitude in stations
            if address not in existing_stations
        )
        session.flush()
