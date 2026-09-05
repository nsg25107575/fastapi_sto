"""create station_customers table

Revision ID: 23993e38369e
Revises: 6c6a33094557
Create Date: 2026-09-03 18:26:37.944994

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '23993e38369e'
down_revision: Union[str, Sequence[str], None] = '6c6a33094557'
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
        sa.ForeignKeyConstraint(['station_id'], ['stations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )
    op.create_index('idx_station_customer_phone', 'station_customers', ['phone'], unique=True, if_not_exists=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_station_customer_phone', table_name='station_customers', if_exists=True)
    op.drop_table('station_customers')

