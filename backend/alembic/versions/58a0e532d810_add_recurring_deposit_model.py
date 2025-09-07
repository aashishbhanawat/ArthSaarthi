"""add recurring deposit model

Revision ID: 58a0e532d810
Revises: c1a3b4d5e6f7
Create Date: 2025-09-07 04:50:03.528718

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.db.custom_types import GUID


# revision identifiers, used by Alembic.
revision: str = '58a0e532d810'
down_revision: Union[str, None] = 'c1a3b4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "recurring_deposits",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("monthly_installment", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("interest_rate", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("tenure_months", sa.Integer(), nullable=False),
        sa.Column("portfolio_id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade():
    op.drop_table("recurring_deposits")