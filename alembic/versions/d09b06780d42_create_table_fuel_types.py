"""create table fuel_types

Revision ID: d09b06780d42
Revises: b894390549dd
Create Date: 2026-10-16 10:46:50.606336

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd09b06780d42'
down_revision: Union[str, Sequence[str], None] = 'b894390549dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'fuel_types',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )
    op.create_index('idx_fuel_type_name', 'fuel_types', ['name'], unique=True, if_not_exists=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_fuel_type_name', table_name='fuel_types')
    op.drop_table('fuel_types')
