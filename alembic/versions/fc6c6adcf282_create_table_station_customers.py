"""create table station_customers

Revision ID: fc6c6adcf282
Revises: e986366661af
Create Date: 2026-10-16 11:03:58.866318

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'fc6c6adcf282'
down_revision: Union[str, Sequence[str], None] = 'e986366661af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'station_customers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('station_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('problem_description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['station_id'], ['stations.id'], name='fk_station_customers_station_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_station_customers_user_id'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )

    op.create_index('idx_station_customer_phone', 'station_customers', ['phone'], unique=True, if_not_exists=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_station_customers_station_id', 'station_customers', type_='foreignkey')
    op.drop_constraint('fk_station_customers_user_id', 'station_customers', type_='foreignkey')
    op.drop_index('idx_station_customer_phone', table_name='station_customers', if_exists=True)
    op.drop_table('station_customers')
