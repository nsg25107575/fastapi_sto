"""create table station_services

Revision ID: 0a716a0c03ef
Revises: 3d868af4169d
Create Date: 2026-10-16 10:57:50.982145

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0a716a0c03ef'
down_revision: Union[str, Sequence[str], None] = '3d868af4169d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'station_services',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('station_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['station_id'], ['stations.id'], name='fk_station_services_station_id'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )

    op.create_index('idx_station_service_name', 'station_services', ['name'], unique=False, if_not_exists=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_station_services_station_id', 'station_services', type_='foreignkey')
    op.drop_index('idx_station_service_name', table_name='station_services', if_exists=True)
    op.drop_table('station_services')
