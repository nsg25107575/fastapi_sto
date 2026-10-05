"""create chat_messages table

Revision ID: 98d3653b816f
Revises: 92dffd9dd999
Create Date: 2026-10-05 14:01:24.818887

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '98d3653b816f'
down_revision: Union[str, Sequence[str], None] = '92dffd9dd999'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('chat_messages',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                    sa.Column('chat_room_id', sa.Integer(), nullable=False),
                    sa.Column('message_type',
                              sa.Enum('system', 'user', name='messagetype', native_enum=False, length=10),
                              nullable=False),
                    sa.Column('sender_type',
                              sa.Enum('customer', 'station', 'system', name='sendertype', native_enum=False, length=10),
                              nullable=False),
                    sa.Column('sender_id', sa.Integer(), nullable=True),
                    sa.Column('body', sa.Text(), nullable=False),
                    sa.Column('attachment_url', sa.Text(), nullable=True),
                    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'),
                              nullable=False),
                    sa.ForeignKeyConstraint(['chat_room_id'], ['chat_rooms.id'], name="fk_chat_messages_chat_room_id"),
                    sa.Index('message_type_index', 'message_type'),
                    sa.Index('sender_type_index', 'sender_type'),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_chat_messages_chat_room_id', 'chat_messages', type_='foreignkey')
    op.drop_index('message_type_index', table_name='chat_messages', if_exists=True)
    op.drop_index('sender_type_index', table_name='chat_messages', if_exists=True)
    op.drop_table('chat_messages')
