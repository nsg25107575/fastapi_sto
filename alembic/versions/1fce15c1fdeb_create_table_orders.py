"""create table orders

Revision ID: 1fce15c1fdeb
Revises: fc6c6adcf282
Create Date: 2026-10-16 11:06:00.418876

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '1fce15c1fdeb'
down_revision: Union[str, Sequence[str], None] = 'fc6c6adcf282'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("station_service_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("cancelled_by", sa.Enum("customer", "station", native_enum=False, length=20, ), nullable=True, ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"),
                  nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"),
                  nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], name="fk_orders_customer_id"),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"], name="fk_orders_station_id"),
        sa.ForeignKeyConstraint(["station_service_id"], ["station_services.id"], name="fk_orders_station_service_id"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )

    op.create_index("idx_order_station_id", "orders", ["station_id"], unique=False, if_not_exists=True)
    op.create_index("idx_order_customer_id", "orders", ["customer_id"], unique=False, if_not_exists=True)
    op.create_index("idx_order_status", "orders", ["status"], unique=False, if_not_exists=True)
    op.create_index("idx_order_cancelled_by", "orders", ["cancelled_by"], unique=False, if_not_exists=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_orders_customer_id", "orders", type_="foreignkey")
    op.drop_constraint("fk_orders_station_id", "orders", type_="foreignkey")
    op.drop_constraint("fk_orders_station_service_id", "orders", type_="foreignkey")
    op.drop_index("idx_order_customer_id", table_name="orders", if_exists=True)
    op.drop_index("idx_order_station_id", table_name="orders", if_exists=True)
    op.drop_index("idx_order_status", table_name="orders", if_exists=True)
    op.drop_index("idx_order_cancelled_by", table_name="orders", if_exists=True)
    op.drop_table("orders")
