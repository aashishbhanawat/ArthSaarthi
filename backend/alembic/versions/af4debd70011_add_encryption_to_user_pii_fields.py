"""Add encryption to user PII fields

Revision ID: af4debd70011
Revises: 45a27f01f9a8
Create Date: 2025-08-15 05:53:08.008306

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af4debd70011'
down_revision: Union[str, None] = '45a27f01f9a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name

    if dialect == 'postgresql':
        pass
    else:
        # SQLite-compatible batch mode
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.alter_column('full_name',
                   existing_type=sa.String(),
                   type_=sa.LargeBinary(),
                   existing_nullable=True)
            batch_op.alter_column('email',
                   existing_type=sa.String(),
                   type_=sa.LargeBinary(),
                   existing_nullable=False)


def downgrade() -> None:
    dialect = op.get_bind().dialect.name

    if dialect == 'postgresql':
        pass
    else:
        # SQLite-compatible batch mode
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.alter_column('email',
                   existing_type=sa.LargeBinary(),
                   type_=sa.String(),
                   existing_nullable=False)
            batch_op.alter_column('full_name',
                   existing_type=sa.LargeBinary(),
                   type_=sa.String(),
                   existing_nullable=True)