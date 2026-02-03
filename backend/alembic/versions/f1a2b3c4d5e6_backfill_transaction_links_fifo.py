"""Backfill transaction links for unlinked sells using FIFO

Revision ID: f1a2b3c4d5e6
Revises: e3f4a5b6c7d8
Create Date: 2026-01-24 05:00:00.000000

"""
from typing import Sequence, Union
from decimal import Decimal
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy import select, insert
from sqlalchemy.orm import Session


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e3f4a5b6c7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Backfill TransactionLinks for existing unlinked SELL transactions using FIFO.
    This ensures capital gains calculations work for historically imported data.
    """
    connection = op.get_bind()

    # Define table references for raw SQL operations
    transactions = sa.table(
        'transactions',
        sa.column('id', sa.String),
        sa.column('user_id', sa.String),
        sa.column('asset_id', sa.String),
        sa.column('portfolio_id', sa.String),
        sa.column('transaction_type', sa.String),
        sa.column('quantity', sa.Numeric),
        sa.column('price_per_unit', sa.Numeric),
        sa.column('transaction_date', sa.DateTime),
    )

    transaction_links = sa.table(
        'transaction_links',
        sa.column('id', sa.String),
        sa.column('sell_transaction_id', sa.String),
        sa.column('buy_transaction_id', sa.String),
        sa.column('quantity', sa.Numeric),
    )

    # Find all SELL transactions without links
    unlinked_sells_query = """
        SELECT t.id, t.user_id, t.asset_id, t.quantity, t.transaction_date
        FROM transactions t
        LEFT JOIN transaction_links tl ON t.id = tl.sell_transaction_id
        WHERE t.transaction_type = 'SELL'
          AND tl.id IS NULL
        ORDER BY t.transaction_date
    """
    unlinked_sells = connection.execute(sa.text(unlinked_sells_query)).fetchall()

    print(f"Found {len(unlinked_sells)} unlinked SELL transactions to backfill")

    for sell in unlinked_sells:
        sell_id, user_id, asset_id, sell_qty, sell_date = sell

        # Get available lots using FIFO (oldest first)
        available_lots_query = """
            WITH buy_lots AS (
                SELECT id, quantity, transaction_date
                FROM transactions
                WHERE user_id = :user_id
                  AND asset_id = :asset_id
                  AND transaction_type IN ('BUY', 'ESPP_PURCHASE', 'RSU_VEST', 'BONUS')
                  AND transaction_date < :sell_date
            ),
            linked_quantities AS (
                SELECT tl.buy_transaction_id, COALESCE(SUM(tl.quantity), 0) as linked_qty
                FROM transaction_links tl
                JOIN buy_lots bl ON tl.buy_transaction_id = bl.id
                GROUP BY tl.buy_transaction_id
            )
            SELECT bl.id, bl.quantity - COALESCE(lq.linked_qty, 0) as available_qty, bl.transaction_date
            FROM buy_lots bl
            LEFT JOIN linked_quantities lq ON bl.id = lq.buy_transaction_id
            WHERE bl.quantity - COALESCE(lq.linked_qty, 0) > 0
            ORDER BY bl.transaction_date
        """
        lots = connection.execute(
            sa.text(available_lots_query),
            {"user_id": str(user_id), "asset_id": str(asset_id), "sell_date": sell_date}
        ).fetchall()

        remaining_qty = Decimal(str(sell_qty))
        for lot in lots:
            if remaining_qty <= 0:
                break
            lot_id, available_qty, lot_date = lot
            take_qty = min(Decimal(str(available_qty)), remaining_qty)
            if take_qty > 0:
                link_id = str(uuid.uuid4())
                connection.execute(
                    sa.text("""
                        INSERT INTO transaction_links (id, sell_transaction_id, buy_transaction_id, quantity)
                        VALUES (:id, :sell_id, :buy_id, :quantity)
                    """),
                    {
                        "id": link_id,
                        "sell_id": str(sell_id),
                        "buy_id": str(lot_id),
                        "quantity": float(take_qty)
                    }
                )
                remaining_qty -= take_qty
                print(f"  Linked {take_qty} from lot {lot_id} (date: {lot_date})")

        if remaining_qty > 0:
            print(f"  WARNING: Could not fully link SELL {sell_id}. Remaining: {remaining_qty}")

    print("Backfill migration complete")


def downgrade() -> None:
    """
    Remove auto-generated links. This is a data migration, so downgrade
    would remove links that were created by this migration.
    Note: This is a best-effort downgrade and may remove manually created links.
    """
    # We don't have a reliable way to identify only auto-generated links,
    # so we leave them in place on downgrade.
    pass
