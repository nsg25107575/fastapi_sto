"""add cancelled_by to orders

Revision ID: 843e59255507
Revises: 8a7dca5fb0f1
Create Date: 2026-10-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "843e59255507"
down_revision: Union[str, Sequence[str], None] = "8a7dca5fb0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add cancelled_by column to orders."""
    op.add_column(
        "orders",
        sa.Column(
            "cancelled_by",
            sa.Enum(
                "customer",
                "station",
                native_enum=False,
                length=20,
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove cancelled_by column from orders."""
    op.drop_column("orders", "cancelled_by")
