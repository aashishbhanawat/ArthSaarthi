"""Add tax_deductions table for Chapter VI-A deductions

Revision ID: h89a0b1c2d3e
Revises: g78f9a0b1c2d
Create Date: 2026-08-27 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.db.custom_types import GUID, EncryptedString

# revision identifiers, used by Alembic.
revision: str = 'h89a0b1c2d3e'
down_revision: Union[str, None] = 'g78f9a0b1c2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tax_deductions',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), nullable=False),
        sa.Column('financial_year', sa.String(), nullable=False),
        sa.Column('section', sa.String(), nullable=False),
        sa.Column('title', EncryptedString(), nullable=False),
        sa.Column('amount', EncryptedString(), nullable=False),
        sa.Column('deduction_date', sa.Date(), nullable=False),
        sa.Column('proof_notes', EncryptedString(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tax_deductions_user_id'), 'tax_deductions', ['user_id'], unique=False)
    op.create_index(op.f('ix_tax_deductions_financial_year'), 'tax_deductions', ['financial_year'], unique=False)
    op.create_index(op.f('ix_tax_deductions_section'), 'tax_deductions', ['section'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tax_deductions_section'), table_name='tax_deductions')
    op.drop_index(op.f('ix_tax_deductions_financial_year'), table_name='tax_deductions')
    op.drop_index(op.f('ix_tax_deductions_user_id'), table_name='tax_deductions')
    op.drop_table('tax_deductions')
