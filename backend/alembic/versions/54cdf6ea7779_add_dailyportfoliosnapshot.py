"""Add DailyPortfolioSnapshot

Revision ID: 54cdf6ea7779
Revises: f1a2b3c4d5e6
Create Date: 2026-02-23 07:10:47.823266

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '54cdf6ea7779'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('daily_portfolio_snapshots',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('portfolio_id', sa.UUID(), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('total_value', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('equity_value', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('mf_value', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('bond_value', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('fd_value', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('holdings_snapshot', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('portfolio_id', 'snapshot_date', name='uq_portfolio_date_snapshot')
    )
    op.create_index(op.f('ix_daily_portfolio_snapshots_portfolio_id'), 'daily_portfolio_snapshots', ['portfolio_id'], unique=False)
    op.create_index(op.f('ix_daily_portfolio_snapshots_snapshot_date'), 'daily_portfolio_snapshots', ['snapshot_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_daily_portfolio_snapshots_snapshot_date'), table_name='daily_portfolio_snapshots')
    op.drop_index(op.f('ix_daily_portfolio_snapshots_portfolio_id'), table_name='daily_portfolio_snapshots')
    op.drop_table('daily_portfolio_snapshots')