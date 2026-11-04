"""Add scheduled_job_logs table

Revision ID: k11d3e4f5g6h
Revises: j10c2d3e4f5g
Create Date: 2026-11-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.db.custom_types import GUID

# revision identifiers, used by Alembic.
revision: str = 'k11d3e4f5g6h'
down_revision: Union[str, None] = 'j10c2d3e4f5g'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'scheduled_job_logs',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('job_id', sa.String(length=100), nullable=False),
        sa.Column('job_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_time_seconds', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_scheduled_job_logs_job_id'),
        'scheduled_job_logs',
        ['job_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_scheduled_job_logs_status'),
        'scheduled_job_logs',
        ['status'],
        unique=False
    )
    op.create_index(
        op.f('ix_scheduled_job_logs_created_at'),
        'scheduled_job_logs',
        ['created_at'],
        unique=False
    )
    op.create_index(
        'idx_job_logs_job_id_status',
        'scheduled_job_logs',
        ['job_id', 'status'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('idx_job_logs_job_id_status', table_name='scheduled_job_logs')
    op.drop_index(op.f('ix_scheduled_job_logs_created_at'), table_name='scheduled_job_logs')
    op.drop_index(op.f('ix_scheduled_job_logs_status'), table_name='scheduled_job_logs')
    op.drop_index(op.f('ix_scheduled_job_logs_job_id'), table_name='scheduled_job_logs')
    op.drop_table('scheduled_job_logs')
