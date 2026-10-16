"""create table order_history

Revision ID: f6e800797080
Revises: 1fce15c1fdeb
Create Date: 2026-10-16 14:05:52.015710

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f6e800797080'
down_revision: Union[str, Sequence[str], None] = '1fce15c1fdeb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "order_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=256), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], name="fk_order_history_order_id"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_order_history_order_id", "order_history", type_="foreignkey")
    op.drop_table("order_history")
