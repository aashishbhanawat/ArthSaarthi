"""Add expected_return to goals

Revision ID: c7e8f9a0b1c2
Revises: f37b332d8eb2
Create Date: 2026-07-21 21:37:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7e8f9a0b1c2'
down_revision: Union[str, None] = 'f37b332d8eb2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('goals', sa.Column('expected_return', sa.Numeric(precision=5, scale=2), nullable=True))


def downgrade() -> None:
    op.drop_column('goals', 'expected_return')
