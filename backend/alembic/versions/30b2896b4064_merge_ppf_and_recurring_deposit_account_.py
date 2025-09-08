"""merge ppf and recurring deposit account number

Revision ID: 30b2896b4064
Revises: 2fc13ed78a51, 719dbe1deafc
Create Date: 2025-09-08 08:57:03.848428

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '30b2896b4064'
down_revision: Union[str, None] = ('2fc13ed78a51', '719dbe1deafc')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass