"""create table vehicles

Revision ID: 24fdaf25313e
Revises: d09b06780d42
Create Date: 2026-10-16 10:48:47.231104

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '24fdaf25313e'
down_revision: Union[str, Sequence[str], None] = 'd09b06780d42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'vehicles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('fuel_type_id', sa.Integer(), server_default=sa.text('1'), nullable=False),
        sa.Column('make', sa.String(length=100), nullable=False),  # Make of the vehicle (e.g., Toyota, Ford)
        sa.Column('model', sa.String(length=100), nullable=False),  # Model of the vehicle (e.g., Camry, F-150)
        sa.Column('year', sa.Integer(), nullable=False),  # Year of manufacture of the vehicle
        sa.Column('license_plate', sa.String(length=20), nullable=False),  # License plate number of the vehicle
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_vehicles_user_id'),
        sa.ForeignKeyConstraint(['fuel_type_id'], ['fuel_types.id'], name='fk_vehicles_fuel_type_id'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_vehicles_user_id', 'vehicles', type_='foreignkey')
    op.drop_constraint('fk_vehicles_fuel_type_id', 'vehicles', type_='foreignkey')

    op.drop_table('vehicles')
