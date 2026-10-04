"""add fake station services

Revision ID: 0537db0b677c
Revises: 82864b230ebc
Create Date: 2026-09-17 13:43:01.465706

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0537db0b677c"
down_revision: Union[str, Sequence[str], None] = "82864b230ebc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    stations_table = sa.table(
        "stations",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("address", sa.String),
    )

    station_services_table = sa.table(
        "station_services",
        sa.column("station_id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("price", sa.Float),
    )

    connection = op.get_bind()

    stations = connection.execute(
        sa.select(
            stations_table.c.id,
            stations_table.c.name,
            stations_table.c.address,
        ).where(
            stations_table.c.name.like("Fake STO %"),
            stations_table.c.address.like("Fake address %"),
        )
    ).fetchall()

    services_by_station = {
        "Fake STO 1": [
            "Oil change",
            "Tire fitting",
            "Engine diagnostics",
        ],
        "Fake STO 2": [
            "Brake repair",
            "Suspension repair",
            "Wheel alignment",
        ],
        "Fake STO 3": [
            "Oil change",
            "Battery replacement",
            "Electrical diagnostics",
        ],
        "Fake STO 4": [
            "Tire fitting",
            "Wheel alignment",
            "Suspension repair",
        ],
        "Fake STO 5": [
            "Engine diagnostics",
            "Brake repair",
            "Oil change",
        ],
        "Fake STO 6": [
            "Battery replacement",
            "Electrical diagnostics",
            "Brake repair",
        ],
        "Fake STO 7": [
            "Suspension repair",
            "Tire fitting",
            "Oil change",
        ],
        "Fake STO 8": [
            "Engine diagnostics",
            "Wheel alignment",
            "Battery replacement",
        ],
        "Fake STO 9": [
            "Brake repair",
            "Suspension repair",
            "Electrical diagnostics",
        ],
        "Fake STO 10": [
            "Oil change",
            "Tire fitting",
            "Engine diagnostics",
            "Brake repair",
        ],
    }

    services = []

    for station in stations:
        station_services = services_by_station.get(
            station.name,
            []
        )

        for service_name in station_services:
            services.append(
                {
                    "station_id": station.id,
                    "name": service_name,
                    "price": None,
                }
            )

    if services:
        op.bulk_insert(
            station_services_table,
            services
        )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE
            FROM station_services
            WHERE station_id IN (SELECT id
                                 FROM stations
                                 WHERE name LIKE 'Fake STO %'
                                   AND address LIKE 'Fake address %')
            """
        )
    )
