"""create customers table

Revision ID: 9958ff5b25e3
Revises: 5c49370dc158
Create Date: 2026-09-15 12:35:41.682179

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9958ff5b25e3'
down_revision: Union[str, Sequence[str], None] = '5c49370dc158'
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
