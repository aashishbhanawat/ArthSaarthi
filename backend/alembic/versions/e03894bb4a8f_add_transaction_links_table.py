"""Add transaction_links table

Revision ID: e03894bb4a8f
Revises: 83bb9e0f1bca
Create Date: 2025-12-14 04:40:19.706061

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.db import custom_types


# revision identifiers, used by Alembic.
revision: str = 'e03894bb4a8f'
down_revision: Union[str, None] = '83bb9e0f1bca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('transaction_links',
    sa.Column('id', custom_types.GUID(), nullable=False),
    sa.Column('sell_transaction_id', custom_types.GUID(), nullable=False),
    sa.Column('buy_transaction_id', custom_types.GUID(), nullable=False),
    sa.Column('quantity', sa.Numeric(precision=18, scale=8), nullable=False),
    sa.ForeignKeyConstraint(['buy_transaction_id'], ['transactions.id'], ),
    sa.ForeignKeyConstraint(['sell_transaction_id'], ['transactions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('transaction_links')
