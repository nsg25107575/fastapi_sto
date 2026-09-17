"""add fake stations

Revision ID: 346860061363
Revises: 7c2a04b52af4
Create Date: 2026-09-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "346860061363"
down_revision: Union[str, Sequence[str], None] = "7c2a04b52af4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    stations = [
        {
            "name": "Fake STO 1",
            "address": "Fake address 1",
            "latitude": 50.76534169202580,
            "longitude": 36.86407988896678,
        },
        {
            "name": "Fake STO 2",
            "address": "Fake address 2",
            "latitude": 50.23771693003254,
            "longitude": 27.80164308785165,
        },
        {
            "name": "Fake STO 3",
            "address": "Fake address 3",
            "latitude": 51.64907669632324,
            "longitude": 31.72529933287856,
        },
        {
            "name": "Fake STO 4",
            "address": "Fake address 4",
            "latitude": 47.03098189248659,
            "longitude": 32.50641781499586,
        },
        {
            "name": "Fake STO 5",
            "address": "Fake address 5",
            "latitude": 46.54994507617364,
            "longitude": 34.82394380131409,
        },
        {
            "name": "Fake STO 6",
            "address": "Fake address 6",
            "latitude": 45.81549493700197,
            "longitude": 35.19024362695215,
        },
        {
            "name": "Fake STO 7",
            "address": "Fake address 7",
            "latitude": 47.26836163358084,
            "longitude": 37.14994791756348,
        },
        {
            "name": "Fake STO 8",
            "address": "Fake address 8",
            "latitude": 50.37421709541349,
            "longitude": 35.25932160736118,
        },
        {
            "name": "Fake STO 9",
            "address": "Fake address 9",
            "latitude": 44.91570090792951,
            "longitude": 27.73451499183379,
        },
        {
            "name": "Fake STO 10",
            "address": "Fake address 10",
            "latitude": 44.07784499128130,
            "longitude": 29.15897240783770,
        },
    ]

    stations_table = sa.table(
        "stations",
        sa.column("name", sa.String),
        sa.column("address", sa.String),
        sa.column("latitude", sa.Numeric(16, 14)),
        sa.column("longitude", sa.Numeric(16, 14)),
    )

    op.bulk_insert(stations_table, stations)


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM stations
            WHERE name LIKE 'Fake STO %'
              AND address LIKE 'Fake address %'
            """
        )
    )
