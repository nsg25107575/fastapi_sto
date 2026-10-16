"""create stations table

Revision ID: ad08b14119de
Revises: 
Create Date: 2026-09-03 17:19:38.732460

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ad08b14119de'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'stations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('address', sa.String(length=200), nullable=False),
        sa.Column('active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('moderation_status', sa.Enum('pending', 'approved', 'rejected', native_enum=False, length=20),
                  server_default=sa.text("'pending'"), nullable=False),
        sa.Column("rejection_reason", sa.String(length=255), nullable=True),
        sa.Column('latitude', sa.Numeric(precision=16, scale=14), nullable=True),
        sa.Column('longitude', sa.Numeric(precision=16, scale=14), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'address', name='uq_station_name_per_address'),
        if_not_exists=True
    )
    op.create_index('idx_station_name', 'stations', ['name'], unique=False, if_not_exists=True)
    op.create_index('idx_station_address', 'stations', ['address'], unique=False, if_not_exists=True)
    op.create_index('idx_station_longitude_latitude', 'stations', ['longitude', 'latitude'], unique=False,
                    if_not_exists=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_station_longitude_latitude', table_name='stations', if_exists=True)
    op.drop_index('idx_station_address', table_name='stations', if_exists=True)
    op.drop_index('idx_station_name', table_name='stations', if_exists=True)
    op.drop_table('stations')
