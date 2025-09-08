"""Add account_number to recurring_deposit

Revision ID: 2fc13ed78a51
Revises: 58a0e532d810
Create Date: 2025-09-07 19:35:16.622628

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2fc13ed78a51'
down_revision: Union[str, None] = '58a0e532d810'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('recurring_deposits', sa.Column('account_number', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('recurring_deposits', 'account_number')