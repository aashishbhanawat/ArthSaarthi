"""Merge audit logging and goal planning branches

Revision ID: b9a8d7c6e5f4
Revises: 067d0411efbc, e4a2b1d8c3f9
Create Date: 2025-08-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9a8d7c6e5f4'
down_revision: Union[str, None, Sequence[str]] = ('067d0411efbc', 'b649d33505f4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass