"""create table customers

Revision ID: e986366661af
Revises: 617deeae03ff
Create Date: 2026-10-16 11:02:34.816322

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e986366661af'
down_revision: Union[str, Sequence[str], None] = '617deeae03ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ip", sa.String(length=45), nullable=False),
        sa.Column("device_hash", sa.String(length=36), nullable=False),
        sa.Column("lat", sa.Numeric(precision=16, scale=14), nullable=False),
        sa.Column("lng", sa.Numeric(precision=16, scale=14), nullable=False),
        sa.Column("public_data", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("customers")
