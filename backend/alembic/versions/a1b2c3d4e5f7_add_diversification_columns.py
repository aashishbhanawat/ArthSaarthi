"""Add sector, industry, country, market_cap to assets

Revision ID: a1b2c3d4e5f7
Revises: e03894bb4a8f
Create Date: 2025-12-31 07:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = 'e03894bb4a8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('assets', sa.Column('sector', sa.String(), nullable=True))
    op.add_column('assets', sa.Column('industry', sa.String(), nullable=True))
    op.add_column('assets', sa.Column('country', sa.String(), nullable=True))
    op.add_column('assets', sa.Column('market_cap', sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column('assets', 'market_cap')
    op.drop_column('assets', 'country')
    op.drop_column('assets', 'industry')
    op.drop_column('assets', 'sector')
