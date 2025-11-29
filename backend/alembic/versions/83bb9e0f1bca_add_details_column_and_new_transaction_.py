"""Add details column and new transaction types

Revision ID: 83bb9e0f1bca
Revises: bbecc17535a9
Create Date: 2025-11-29 04:36:55.364937

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '83bb9e0f1bca'
down_revision: Union[str, None] = 'bbecc17535a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('transactions', sa.Column('details', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('transactions', 'details')
