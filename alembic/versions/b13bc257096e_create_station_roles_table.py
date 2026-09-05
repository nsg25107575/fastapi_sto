"""create station_roles table

Revision ID: b13bc257096e
Revises: 3f2d4d5ec174
Create Date: 2026-09-03 19:04:23.952601

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'b13bc257096e'
down_revision: Union[str, Sequence[str], None] = '3f2d4d5ec174'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    table = op.create_table(
        'station_roles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )
    op.bulk_insert(table, [
        {'name': 'Manager', 'description': 'Responsible for overall station management and operations.'},
        {'name': 'Cashier', 'description': 'Handles cash transactions and customer payments.'},
        {'name': 'Fuel Attendant',
         'description': 'Assists customers with fueling their vehicles and maintaining the fuel pumps.'},
        {'name': 'Maintenance Staff',
         'description': 'Responsible for maintaining and repairing station equipment and facilities.'},
        {'name': 'Security Personnel',
         'description': 'Ensures the safety and security of the station premises and customers.'},
    ])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('station_roles')
