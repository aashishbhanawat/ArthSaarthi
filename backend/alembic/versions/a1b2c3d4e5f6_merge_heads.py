"""merge heads

Revision ID: a1b2c3d4e5f6
Revises: ('993569e6612d', 'b9e6a3a9a1e1')
Create Date: 2025-08-23 06:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = ('993569e6612d', 'b9e6a3a9a1e1')
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
