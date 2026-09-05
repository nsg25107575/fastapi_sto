"""create station_cantacts table

Revision ID: 187f073f13e8
Revises: ad08b14119de
Create Date: 2026-09-03 17:24:23.512093

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '187f073f13e8'
down_revision: Union[str, Sequence[str], None] = 'ad08b14119de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'station_contacts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('station_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['station_id'], ['stations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )
    op.create_index(op.f('idx_station_contact_type'), 'station_contacts', ['type'], unique=False, if_not_exists=True)
    op.create_index(op.f('idx_station_contact_value'), 'station_contacts', ['value'], unique=False, if_not_exists=True)



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('idx_station_contact_value'), table_name='station_contacts', if_exists=True)
    op.drop_index(op.f('idx_station_contact_type'), table_name='station_contacts', if_exists=True)
    op.drop_table('station_contacts')
