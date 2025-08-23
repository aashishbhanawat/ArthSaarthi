"""merge heads

Revision ID: d110a2d98765
Revises: ('993569e6612d', 'b9e6a3a9a1e1')
Create Date: 2025-08-23 06:38:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd110a2d98765'
down_revision: Union[str, None] = ('993569e6612d', 'b9e6a3a9a1e1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
