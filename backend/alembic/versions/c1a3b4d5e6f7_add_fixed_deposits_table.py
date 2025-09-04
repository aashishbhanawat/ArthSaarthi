"""add fixed_deposits table

Revision ID: c1a3b4d5e6f7
Revises: b9a8d7c6e5f4
Create Date: 2025-09-04 09:06:53.123456

"""
from alembic import op
import sqlalchemy as sa
from app.db.custom_types import GUID


# revision identifiers, used by Alembic.
revision = 'c1a3b4d5e6f7'
down_revision = 'b9a8d7c6e5f4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'fixed_deposits',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('principal_amount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('interest_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('maturity_date', sa.Date(), nullable=False),
        sa.Column('compounding_frequency', sa.String(), server_default='Annually', nullable=False),
        sa.Column('interest_payout', sa.String(), server_default='Cumulative', nullable=False),
        sa.Column('portfolio_id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), nullable=False),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('fixed_deposits')
