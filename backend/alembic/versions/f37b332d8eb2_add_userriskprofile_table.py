"""Add UserRiskProfile table

Revision ID: f37b332d8eb2
Revises: 54cdf6ea7779
Create Date: 2026-07-14 15:45:54.766738

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from app.db.custom_types import GUID, EncryptedString


# revision identifiers, used by Alembic.
revision: str = 'f37b332d8eb2'
down_revision: Union[str, None] = '54cdf6ea7779'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_risk_profiles',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), nullable=False),
        sa.Column('answers', EncryptedString(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('risk_category', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade() -> None:
    op.drop_table('user_risk_profiles')