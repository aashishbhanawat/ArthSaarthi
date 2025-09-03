"""Add portfolio_id to assets

Revision ID: 3b2c1d4e5f6a
Revises: 2a1b3c4d5e6f
Create Date: 2025-09-02 21:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.db.custom_types import GUID


# revision identifiers, used by Alembic.
revision: str = '3b2c1d4e5f6a'
down_revision: Union[str, None] = '2a1b3c4d5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('assets', sa.Column('portfolio_id', GUID(), sa.ForeignKey('portfolios.id'), nullable=True))


def downgrade() -> None:
    op.drop_column('assets', 'portfolio_id')
