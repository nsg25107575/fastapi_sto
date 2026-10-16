"""create table tokens

Revision ID: b795fc1e6c5c
Revises: e55b9d88c3f5
Create Date: 2026-10-16 14:53:53.868153

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b795fc1e6c5c'
down_revision: Union[str, Sequence[str], None] = 'e55b9d88c3f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=512), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_tokens_user_id'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_tokens_user_id', 'tokens', type_='foreignkey')
    op.drop_table('tokens')
