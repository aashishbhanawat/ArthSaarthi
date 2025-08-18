"""Revert user pii encryption for postgres

Revision ID: b5a5e3d7f2c1
Revises: af4debd70011
Create Date: 2025-08-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5a5e3d7f2c1'
down_revision: Union[str, None] = 'af4debd70011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name

    if dialect == 'postgresql':
        op.alter_column('users', 'full_name',
               type_=sa.String(),
               postgresql_using='full_name::varchar')
        op.alter_column('users', 'email',
               type_=sa.String(),
               postgresql_using='email::varchar')


def downgrade() -> None:
    dialect = op.get_bind().dialect.name

    if dialect == 'postgresql':
        op.alter_column('users', 'full_name',
               type_=sa.LargeBinary(),
               postgresql_using='full_name::bytea')
        op.alter_column('users', 'email',
               type_=sa.LargeBinary(),
               postgresql_using='email::bytea')
