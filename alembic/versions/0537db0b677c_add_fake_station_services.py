"""add fake station services

Revision ID: 0537db0b677c
Revises: 82864b230ebc
Create Date: 2026-09-17 13:43:01.465706

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

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
            "Замена масла",
            "Шиномонтаж",
            "Диагностика двигателя",
        ],
        "Fake STO 2": [
            "Ремонт тормозов",
            "Ремонт подвески",
            "Развал-схождение",
        ],
        "Fake STO 3": [
            "Замена масла",
            "Замена аккумулятора",
            "Диагностика электрооборудования",
        ],
        "Fake STO 4": [
            "Шиномонтаж",
            "Развал-схождение",
            "Ремонт подвески",
        ],
        "Fake STO 5": [
            "Диагностика двигателя",
            "Ремонт тормозов",
            "Замена масла",
        ],
        "Fake STO 6": [
            "Замена аккумулятора",
            "Диагностика электрооборудования",
            "Ремонт тормозов",
        ],
        "Fake STO 7": [
            "Ремонт подвески",
            "Шиномонтаж",
            "Замена масла",
        ],
        "Fake STO 8": [
            "Диагностика двигателя",
            "Развал-схождение",
            "Замена аккумулятора",
        ],
        "Fake STO 9": [
            "Ремонт тормозов",
            "Ремонт подвески",
            "Диагностика электрооборудования",
        ],
        "Fake STO 10": [
            "Замена масла",
            "Шиномонтаж",
            "Диагностика двигателя",
            "Ремонт тормозов",
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
            DELETE FROM station_services
            WHERE station_id IN (
                SELECT id
                FROM stations
                WHERE name LIKE 'Fake STO %'
                  AND address LIKE 'Fake address %'
            )
            """
        )
    )
