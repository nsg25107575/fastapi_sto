"""add admin flag to users

Revision ID: db1af956657b
Revises: ea7c5e3fc198
Create Date: 2026-10-15 09:11:06.398116

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "db1af956657b"
down_revision: Union[str, Sequence[str], None] = "ea7c5e3fc198"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add admin flag to users."""
    op.add_column(
        "users",
        sa.Column(
            "is_admin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    """Remove admin flag from users."""
    op.drop_column("users", "is_admin")
