"""Add AssetAlias table

Revision ID: a2b4c6d8e0f1
Revises: 79fbc0246a96
Create Date: 2025-08-10 10:53:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a2b4c6d8e0f1'
down_revision: Union[str, None] = '79fbc0246a96'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('asset_aliases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alias_symbol', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('alias_symbol', 'source', name='_alias_symbol_source_uc')
    )
    op.create_index(op.f('ix_asset_aliases_alias_symbol'), 'asset_aliases', ['alias_symbol'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_asset_aliases_alias_symbol'), table_name='asset_aliases')
    op.drop_table('asset_aliases')
