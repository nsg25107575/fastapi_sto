"""create users table

Revision ID: 0e2859d3a373
Revises: a703cf38f360
Create Date: 2026-09-03 18:12:47.865115

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0e2859d3a373'
down_revision: Union[str, Sequence[str], None] = 'a703cf38f360'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('email_verified', sa.DateTime(), server_default=sa.text('NULL'), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('second_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('password', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), server_default=sa.text('NULL'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        if_not_exists=True
    )
    op.create_index('idx_user_email', 'users', ['email'], unique=True, if_not_exists=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_user_email', table_name='users', if_exists=True)
    op.drop_table('users')
