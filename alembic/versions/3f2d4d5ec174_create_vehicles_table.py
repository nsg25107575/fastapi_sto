"""create vehicles table

Revision ID: 3f2d4d5ec174
Revises: 23993e38369e
Create Date: 2026-09-03 18:44:07.721012

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '3f2d4d5ec174'
down_revision: Union[str, Sequence[str], None] = '23993e38369e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create fuel_types table to store different types of fuel (e.g., Petrol, Diesel, Electric)
    table = op.create_table('fuel_types',
                            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                            sa.Column('name', sa.String(length=100), nullable=False),
                            sa.PrimaryKeyConstraint('id'),
                            if_not_exists=True
                            )
    op.create_index('idx_fuel_type_name', 'fuel_types', ['name'], unique=True, if_not_exists=True)

    # Insert initial fuel types into the fuel_types table
    op.bulk_insert(table, [
        {'name': 'Petrol'},
        {'name': 'Diesel'},
        {'name': 'Electric'},
        {'name': 'Hybrid'},  # Hybrid vehicles that use a combination of fuel and electric power
        {'name': 'CNG'},  # Compressed Natural Gas
        {'name': 'LPG'},  # Liquefied Petroleum Gas
    ])

    # Create vehicles table to store information about vehicles
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
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['fuel_type_id'], ['fuel_types.id'], ),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('vehicles')
    op.drop_index('idx_fuel_type_name', table_name='fuel_types', if_exists=True)
    op.drop_table('fuel_types')

