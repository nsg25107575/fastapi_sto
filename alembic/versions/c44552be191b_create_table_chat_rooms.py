"""create table chat_rooms

Revision ID: c44552be191b
Revises: f6e800797080
Create Date: 2026-10-16 14:33:39.644118

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from models import ChatRoomStatus

# revision identifiers, used by Alembic.
revision: str = 'c44552be191b'
down_revision: Union[str, Sequence[str], None] = 'f6e800797080'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'chat_rooms',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=10), server_default=ChatRoomStatus.ACTIVE, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'),
                  nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'),
                  nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], name='fk_order_id_chatroom_order_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id')
    )

    op.drop_constraint('fk_order_id_chatroom_order_id', 'chat_rooms', type_='foreignkey')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_order_id_chatroom_order_id', 'chat_rooms', type_='foreignkey')
    op.drop_table('chat_rooms')
