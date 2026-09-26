"""Add broker_credentials table

Revision ID: j10c2d3e4f5g
Revises: i90b1c2d3e4f
Create Date: 2026-09-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.db.custom_types import GUID

# revision identifiers, used by Alembic.
revision: str = 'j10c2d3e4f5g'
down_revision: Union[str, None] = 'i90b1c2d3e4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'broker_credentials',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), nullable=False),
        sa.Column('provider_name', sa.String(length=50), nullable=False),
        sa.Column('api_key', sa.String(length=255), nullable=False),
        sa.Column('encrypted_api_secret', sa.Text(), nullable=False),
        sa.Column('encrypted_access_token', sa.Text(), nullable=True),
        sa.Column('token_issued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'provider_name', name='uq_user_provider')
    )
    op.create_index(op.f('ix_broker_credentials_user_id'), 'broker_credentials', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_broker_credentials_user_id'), table_name='broker_credentials')
    op.drop_table('broker_credentials')
