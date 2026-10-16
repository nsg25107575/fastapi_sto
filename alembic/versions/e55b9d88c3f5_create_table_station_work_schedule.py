"""create table station_work_schedule

Revision ID: e55b9d88c3f5
Revises: 6b00420e8e15
Create Date: 2026-10-16 14:52:12.978896

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e55b9d88c3f5'
down_revision: Union[str, Sequence[str], None] = '6b00420e8e15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'station_work_schedule',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('station_id', sa.Integer(), nullable=False),
        sa.Column('flow', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['station_id'], ['stations.id'], name='fk_station_work_schedule_station_id'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_station_work_schedule_station_id', 'station_work_schedule', type_='foreignkey')
    op.drop_table('station_work_schedule')
