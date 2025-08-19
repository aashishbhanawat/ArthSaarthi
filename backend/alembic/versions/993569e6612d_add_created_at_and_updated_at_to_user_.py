"""Add created_at and updated_at to User model

Revision ID: 993569e6612d
Revises: b9e6a3a9a1e1
Create Date: 2025-07-22 16:21:04.298252

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '993569e6612d'
down_revision: Union[str, None] = 'b9e6a3a9a1e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('is_admin',
                   existing_type=sa.BOOLEAN(),
                   nullable=False)
        batch_op.create_index(batch_op.f('ix_users_full_name'), ['full_name'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_full_name'))
        batch_op.alter_column('is_admin',
                   existing_type=sa.BOOLEAN(),
                   nullable=True)