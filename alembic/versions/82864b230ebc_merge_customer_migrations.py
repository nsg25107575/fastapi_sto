"""merge customer migrations

Revision ID: 82864b230ebc
Revises: 346860061363, 9958ff5b25e3
Create Date: 2026-09-17 11:25:40.750730

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82864b230ebc'
down_revision: Union[str, Sequence[str], None] = ('346860061363', '9958ff5b25e3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
