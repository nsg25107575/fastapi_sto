"""create chat rooms

Revision ID: 92dffd9dd999
Revises: a1b2c3d4e5f6
Create Date: 2026-10-05 14:16:17.689855

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '92dffd9dd999'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('chat_rooms',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                    sa.Column('order_id', sa.Integer(), nullable=False),
                    sa.Column('status',
                              sa.Enum('active', 'archived', name='chatroomstatus', native_enum=False, length=10),
                              server_default='active', nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'),
                              nullable=False),
                    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'),
                              nullable=False),
                    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], name='fk_order_id_chatroom_order_id'),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('order_id')
                    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_order_id_chatroom_order_id', 'chat_rooms', type_='foreignkey')
    op.drop_table('chat_rooms')
