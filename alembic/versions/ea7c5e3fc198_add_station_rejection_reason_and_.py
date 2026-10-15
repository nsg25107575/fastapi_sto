"""Add station rejection reason and moderation enum."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "ea7c5e3fc198"
down_revision: Union[str, Sequence[str], None] = "1104cb61b03e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "stations",
        "moderation_status",
        existing_type=sa.String(length=20),
        type_=sa.Enum(
            "pending",
            "approved",
            "rejected",
            native_enum=False,
            length=20,
        ),
        existing_nullable=False,
        existing_server_default=sa.text("'pending'"),
        server_default=sa.text("'pending'"),
    )

    op.add_column(
        "stations",
        sa.Column(
            "rejection_reason",
            sa.String(length=255),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("stations", "rejection_reason")

    op.alter_column(
        "stations",
        "moderation_status",
        existing_type=sa.Enum(
            "pending",
            "approved",
            "rejected",
            native_enum=False,
            length=20,
        ),
        type_=sa.String(length=20),
        existing_nullable=False,
        existing_server_default=sa.text("'pending'"),
        server_default=sa.text("'pending'"),
    )
