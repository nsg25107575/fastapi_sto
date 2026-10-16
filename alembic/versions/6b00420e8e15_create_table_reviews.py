"""create table reviews

Revision ID: 6b00420e8e15
Revises: 302b0917a59c
Create Date: 2026-10-16 14:50:40.622057

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '6b00420e8e15'
down_revision: Union[str, Sequence[str], None] = '302b0917a59c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "reviews",
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"),
                  nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"),
                  nullable=False),
        sa.PrimaryKeyConstraint("order_id", "station_id", "customer_id",
                                name="uq_order_station_customer_review"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], name="fk_reviews_order_id"),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"], name="fk_reviews_station_id"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], name="fk_reviews_customer_id")
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_reviews_order_id", "reviews", type_="foreignkey")
    op.drop_constraint("fk_reviews_station_id", "reviews", type_="foreignkey")
    op.drop_constraint("fk_reviews_customer_id", "reviews", type_="foreignkey")
    op.drop_table("reviews")
