import random

from database import SessionLocal
from models.station import StationModel

USER_LATITUDE = 48.49689099250345
USER_LONGITUDE = 32.23869921769066

FAKE_STATIONS_COUNT = 10
COORDINATE_OFFSET = 5


def create_fake_stations():
    session = SessionLocal()

    try:
        for i in range(1, FAKE_STATIONS_COUNT + 1):
            latitude = USER_LATITUDE + random.uniform(
                -COORDINATE_OFFSET,
                COORDINATE_OFFSET,
            )

            longitude = USER_LONGITUDE + random.uniform(
                -COORDINATE_OFFSET,
                COORDINATE_OFFSET,
            )

            station = StationModel(
                name=f"Fake STO {i}",
                address=f"Fake address {i}",
                latitude=latitude,
                longitude=longitude,
            )

            session.add(station)

        session.commit()

        print(
            f"Successfully created "
            f"{FAKE_STATIONS_COUNT} fake stations."
        )

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    create_fake_stations()
