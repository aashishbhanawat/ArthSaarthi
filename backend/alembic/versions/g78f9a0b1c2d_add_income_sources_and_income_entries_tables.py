"""Add income_sources and income_entries tables

Revision ID: g78f9a0b1c2d
Revises: f67e8f9a0b1c
Create Date: 2026-08-26 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.db.custom_types import GUID, EncryptedString

# revision identifiers, used by Alembic.
revision: str = 'g78f9a0b1c2d'
down_revision: Union[str, None] = 'f67e8f9a0b1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'income_sources',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), nullable=False),
        sa.Column('name', EncryptedString(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('payer_name', EncryptedString(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_income_sources_user_id'), 'income_sources', ['user_id'], unique=False)

    op.create_table(
        'income_entries',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), nullable=False),
        sa.Column('source_id', GUID(), nullable=False),
        sa.Column('financial_year', sa.String(), nullable=False),
        sa.Column('entry_date', sa.Date(), nullable=False),
        sa.Column('gross_amount', EncryptedString(), nullable=False),
        sa.Column('tds_amount', EncryptedString(), nullable=False, server_default='0.00'),
        sa.Column('net_amount', EncryptedString(), nullable=False),
        sa.Column('notes', EncryptedString(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['income_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_income_entries_user_id'), 'income_entries', ['user_id'], unique=False)
    op.create_index(op.f('ix_income_entries_financial_year'), 'income_entries', ['financial_year'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_income_entries_financial_year'), table_name='income_entries')
    op.drop_index(op.f('ix_income_entries_user_id'), table_name='income_entries')
    op.drop_table('income_entries')

    op.drop_index(op.f('ix_income_sources_user_id'), table_name='income_sources')
    op.drop_table('income_sources')
