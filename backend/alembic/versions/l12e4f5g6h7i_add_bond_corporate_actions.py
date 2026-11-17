"""Add bond corporate actions and events table

Revision ID: l12e4f5g6h7i
Revises: k11d3e4f5g6h
Create Date: 2026-11-08 16:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.db.custom_types import GUID

# revision identifiers, used by Alembic.
revision: str = 'l12e4f5g6h7i'
down_revision: Union[str, None] = 'k11d3e4f5g6h'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add is_automated flag to transactions
    op.add_column(
        'transactions',
        sa.Column('is_automated', sa.Boolean(), server_default=sa.text('false'), nullable=False)
    )
    op.create_index(
        op.f('ix_transactions_is_automated'),
        'transactions',
        ['is_automated'],
        unique=False
    )

    # 2. Create corporate_action_events table
    op.create_table(
        'corporate_action_events',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), nullable=False),
        sa.Column('portfolio_id', GUID(), nullable=False),
        sa.Column('asset_id', GUID(), nullable=False),
        sa.Column('transaction_id', GUID(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('units', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('amount', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='NEW', nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'ix_corporate_action_events_user_status',
        'corporate_action_events',
        ['user_id', 'status'],
        unique=False
    )
    op.create_index(
        op.f('ix_corporate_action_events_portfolio_id'),
        'corporate_action_events',
        ['portfolio_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_corporate_action_events_asset_id'),
        'corporate_action_events',
        ['asset_id'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_corporate_action_events_asset_id'), table_name='corporate_action_events')
    op.drop_index(op.f('ix_corporate_action_events_portfolio_id'), table_name='corporate_action_events')
    op.drop_index('ix_corporate_action_events_user_status', table_name='corporate_action_events')
    op.drop_table('corporate_action_events')
    op.drop_index(op.f('ix_transactions_is_automated'), table_name='transactions')
    op.drop_column('transactions', 'is_automated')
