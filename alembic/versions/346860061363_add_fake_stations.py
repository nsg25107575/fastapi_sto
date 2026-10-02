"""add fake stations

Revision ID: 346860061363
Revises: 7c2a04b52af4
Create Date: 2026-09-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from scripts.fake_stations import create_fake_stations

revision: str = "346860061363"
down_revision: Union[str, Sequence[str], None] = "7c2a04b52af4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    create_fake_stations()


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE
            FROM stations
            WHERE name LIKE '%Fake STO%'
              AND address LIKE '%Fake address%'
            """
        )
    )
