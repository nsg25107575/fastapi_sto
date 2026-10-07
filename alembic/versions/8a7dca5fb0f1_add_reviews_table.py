"""add reviews table

Revision ID: 8a7dca5fb0f1
Revises: 98d3653b816f
Create Date: 2026-10-06 18:10:47.522749

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "8a7dca5fb0f1"
down_revision: Union[str, Sequence[str], None] = "98d3653b816f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table("reviews",
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
