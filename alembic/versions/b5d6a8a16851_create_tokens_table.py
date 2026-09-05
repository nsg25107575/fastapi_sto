"""create tokens table

Revision ID: b5d6a8a16851
Revises: b13bc257096e
Create Date: 2026-09-03 19:14:51.800389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'b5d6a8a16851'
down_revision: Union[str, Sequence[str], None] = 'b13bc257096e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('tokens')