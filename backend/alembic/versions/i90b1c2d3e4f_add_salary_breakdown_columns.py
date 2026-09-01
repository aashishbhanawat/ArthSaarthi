"""Add salary breakdown and HRA exemption columns to income_entries

Revision ID: i90b1c2d3e4f
Revises: h89a0b1c2d3e
Create Date: 2026-08-31 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.db.custom_types import EncryptedString

# revision identifiers, used by Alembic.
revision: str = 'i90b1c2d3e4f'
down_revision: Union[str, None] = 'h89a0b1c2d3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('income_entries', sa.Column('basic_amount', EncryptedString(), nullable=True))
    op.add_column('income_entries', sa.Column('hra_amount', EncryptedString(), nullable=True))
    op.add_column('income_entries', sa.Column('da_amount', EncryptedString(), nullable=True))
    op.add_column('income_entries', sa.Column('special_allowance_amount', EncryptedString(), nullable=True))
    op.add_column('income_entries', sa.Column('other_allowances_amount', EncryptedString(), nullable=True))
    op.add_column('income_entries', sa.Column('other_benefits_amount', EncryptedString(), nullable=True))
    op.add_column('income_entries', sa.Column('rent_paid', EncryptedString(), nullable=True))
    op.add_column('income_entries', sa.Column('is_metro', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('income_entries', sa.Column('hra_exemption', EncryptedString(), server_default='0.00', nullable=True))


def downgrade() -> None:
    op.drop_column('income_entries', 'hra_exemption')
    op.drop_column('income_entries', 'is_metro')
    op.drop_column('income_entries', 'rent_paid')
    op.drop_column('income_entries', 'other_benefits_amount')
    op.drop_column('income_entries', 'other_allowances_amount')
    op.drop_column('income_entries', 'special_allowance_amount')
    op.drop_column('income_entries', 'da_amount')
    op.drop_column('income_entries', 'hra_amount')
    op.drop_column('income_entries', 'basic_amount')
