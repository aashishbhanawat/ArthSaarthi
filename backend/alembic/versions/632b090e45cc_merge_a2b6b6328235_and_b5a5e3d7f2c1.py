"""Merge a2b6b6328235 and b5a5e3d7f2c1

Revision ID: 632b090e45cc
Revises: a2b6b6328235, b5a5e3d7f2c1
Create Date: 2025-08-23 16:19:03.243484

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '632b090e45cc'
down_revision: Union[str, None] = ('a2b6b6328235', 'b5a5e3d7f2c1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass