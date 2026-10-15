"""add station moderation status

Revision ID: 1104cb61b03e
Revises: 843e59255507
Create Date: 2026-10-13 11:43:09.364799

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "1104cb61b03e"
down_revision: Union[str, Sequence[str], None] = "843e59255507"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing stations remain approved after adding the column.
    op.add_column(
        "stations",
        sa.Column(
            "moderation_status",
            sa.String(length=20),
            nullable=False,
            server_default="approved",
        ),
    )

    # New stations will be pending by default.
    op.alter_column(
        "stations",
        "moderation_status",
        existing_type=sa.String(length=20),
        existing_nullable=False,
        server_default="pending",
    )


def downgrade() -> None:
    op.drop_column("stations", "moderation_status")
