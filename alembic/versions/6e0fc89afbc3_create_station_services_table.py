"""create station_services table

Revision ID: 6e0fc89afbc3
Revises: 187f073f13e8
Create Date: 2026-09-03 17:32:19.938387

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6e0fc89afbc3'
down_revision: Union[str, Sequence[str], None] = '187f073f13e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'station_services',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('station_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['station_id'], ['stations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )
    op.create_index('idx_station_service_name', 'station_services', ['name'], unique=False, if_not_exists=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_station_service_name', table_name='station_services', if_exists=True)
    op.drop_table('station_services')
