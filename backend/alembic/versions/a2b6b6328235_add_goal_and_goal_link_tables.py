"""add goal and goal_link tables

Revision ID: a2b6b6328235
Revises: f99bfd8a1d75
Create Date: 2025-08-20 21:12:00.000000

"""
from alembic import op
import sqlalchemy as sa
from app.db.custom_types import GUID


# revision identifiers, used by Alembic.
revision = 'a2b6b6328235'
down_revision = 'f99bfd8a1d75'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('goals',
    sa.Column('id', GUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('target_amount', sa.Numeric(), nullable=False),
    sa.Column('target_date', sa.Date(), nullable=False),
    sa.Column('user_id', GUID(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goals_name'), 'goals', ['name'], unique=False)

    op.create_table('goal_links',
    sa.Column('id', GUID(), nullable=False),
    sa.Column('goal_id', GUID(), nullable=False),
    sa.Column('portfolio_id', GUID(), nullable=True),
    sa.Column('asset_id', GUID(), nullable=True),
    sa.Column('user_id', GUID(), nullable=False),
    sa.CheckConstraint('(portfolio_id IS NOT NULL AND asset_id IS NULL) OR (portfolio_id IS NULL AND asset_id IS NOT NULL)', name='check_goal_link_target'),
    sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
    sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ),
    sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('goal_links')
    op.drop_index(op.f('ix_goals_name'), table_name='goals')
    op.drop_table('goals')
