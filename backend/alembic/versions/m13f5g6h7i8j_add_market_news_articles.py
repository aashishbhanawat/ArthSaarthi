"""Add market news articles table for research feed

Revision ID: m13f5g6h7i8j
Revises: l12e4f5g6h7i
Create Date: 2026-11-19 22:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'm13f5g6h7i8j'
down_revision: Union[str, None] = 'l12e4f5g6h7i'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'market_news_articles',
        sa.Column('id', sa.String(length=64), primary_key=True, nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('url', sa.String(length=1000), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=30), server_default='NEWS', nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('symbols', sa.JSON(), nullable=False),
        sa.Column('sentiment', sa.String(length=20), server_default='NEUTRAL', nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_market_news_articles_url'),
        'market_news_articles',
        ['url'],
        unique=True
    )
    op.create_index(
        op.f('ix_market_news_articles_published_at'),
        'market_news_articles',
        ['published_at'],
        unique=False
    )
    op.create_index(
        op.f('ix_market_news_articles_category'),
        'market_news_articles',
        ['category'],
        unique=False
    )
    op.create_index(
        op.f('ix_market_news_articles_source'),
        'market_news_articles',
        ['source'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_market_news_articles_source'), table_name='market_news_articles')
    op.drop_index(op.f('ix_market_news_articles_category'), table_name='market_news_articles')
    op.drop_index(op.f('ix_market_news_articles_published_at'), table_name='market_news_articles')
    op.drop_index(op.f('ix_market_news_articles_url'), table_name='market_news_articles')
    op.drop_table('market_news_articles')
