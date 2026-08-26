"""Add capital_loss_ledgers table

Revision ID: f67e8f9a0b1c
Revises: c7e8f9a0b1c2
Create Date: 2026-08-22 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f67e8f9a0b1c'
down_revision: Union[str, None] = 'c7e8f9a0b1c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'capital_loss_ledgers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('financial_year', sa.String(length=7), nullable=False),
        sa.Column('assessment_year', sa.String(length=7), nullable=False),
        sa.Column('stcl_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.0'),
        sa.Column('ltcl_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.0'),
        sa.Column('is_itr_filed_on_time', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_capital_loss_ledgers_user_id'), 'capital_loss_ledgers', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_capital_loss_ledgers_user_id'), table_name='capital_loss_ledgers')
    op.drop_table('capital_loss_ledgers')
