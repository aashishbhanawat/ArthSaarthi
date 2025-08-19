"""Add source to import sessions

Revision ID: 1c3a7e6d8b5f
Revises: a2b4c6d8e0f1
Create Date: 2025-08-12 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1c3a7e6d8b5f'
down_revision = 'a2b4c6d8e0f1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('import_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source', sa.String(), server_default='Unknown'))

    # Set nullable to False in a separate step if needed, after default is applied
    with op.batch_alter_table('import_sessions', schema=None) as batch_op:
        batch_op.alter_column('source', nullable=False)

def downgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('import_sessions', schema=None) as batch_op:
        batch_op.drop_column('source')
