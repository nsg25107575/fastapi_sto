"""create table station_users

Revision ID: 3d868af4169d
Revises: c6825d3c5b1f
Create Date: 2026-10-16 10:56:00.845002

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3d868af4169d'
down_revision: Union[str, Sequence[str], None] = 'c6825d3c5b1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'station_users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('station_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), server_default=sa.text('1'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['station_id'], ['stations.id'], name='fk_station_users_station_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_station_users_user_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('station_id', 'user_id'),
        if_not_exists=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_station_users_station_id', 'station_users', type_='foreignkey')
    op.drop_constraint('fk_station_users_user_id', 'station_users', type_='foreignkey')
    op.drop_table('station_users')
