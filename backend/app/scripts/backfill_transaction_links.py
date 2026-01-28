"""
Backfill script to create TransactionLinks for existing unlinked SELL transactions.

This script finds all SELL transactions that don't have TransactionLinks and
creates them using FIFO (First-In-First-Out) matching against available BUY lots.

Run via:
docker compose run --rm backend python app/scripts/backfill_transaction_links.py
"""
import logging
import sys
from decimal import Decimal

# Add app to path
sys.path.insert(0, "/app")

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.transaction import Transaction
from app.models.transaction_link import TransactionLink
from app.schemas.enums import TransactionType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_available_lots_for_backfill(
    db: Session, user_id, asset_id, before_date
) -> list[dict]:
    """
    Get available BUY lots for an asset as of a specific date.
    Similar to CRUDTransaction.get_available_lots but filters by date.
    """
    transactions = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.asset_id == asset_id,
            Transaction.transaction_date < before_date,
            Transaction.transaction_type.in_(
                ["BUY", "ESPP_PURCHASE", "RSU_VEST", "SELL", "BONUS"]
            ),
        )
        .order_by(Transaction.transaction_date)
        .all()
    )

    lots = []

    for tx in transactions:
        if tx.transaction_type in ["BUY", "ESPP_PURCHASE", "RSU_VEST", "BONUS"]:
            lots.append({
                "id": tx.id,
                "available_quantity": tx.quantity,
                "date": tx.transaction_date,
                "price_per_unit": tx.price_per_unit,
            })
        elif tx.transaction_type == "SELL":
            sell_qty = tx.quantity

            # 1. Process existing links
            links = (
                db.query(TransactionLink)
                .filter(TransactionLink.sell_transaction_id == tx.id)
                .all()
            )
            for link in links:
                sell_qty -= link.quantity
                for lot in lots:
                    if lot["id"] == link.buy_transaction_id:
                        lot["available_quantity"] -= link.quantity
                        break

            # 2. Process unlinked quantity via FIFO
            if sell_qty > 0:
                for lot in lots:
                    if lot["available_quantity"] > 0:
                        take = min(lot["available_quantity"], sell_qty)
                        lot["available_quantity"] -= take
                        sell_qty -= take
                        if sell_qty <= 0:
                            break

    return [lot for lot in lots if lot["available_quantity"] > 0]


def backfill_links():
    db = SessionLocal()
    try:
        # Find all SELL transactions without links
        sell_txs = (
            db.query(Transaction)
            .outerjoin(
                TransactionLink,
                Transaction.id == TransactionLink.sell_transaction_id
            )
            .filter(
                Transaction.transaction_type == TransactionType.SELL,
                TransactionLink.id.is_(None)  # No existing links
            )
            .order_by(Transaction.transaction_date)
            .all()
        )

        logger.info(f"Found {len(sell_txs)} unlinked SELL transactions")

        created_count = 0
        for sell_tx in sell_txs:
            logger.info(
                f"Processing SELL: {sell_tx.id} - "
                f"Asset: {sell_tx.asset_id}, Qty: {sell_tx.quantity}, "
                f"Date: {sell_tx.transaction_date}"
            )

            # Get available lots as of sell date
            available_lots = get_available_lots_for_backfill(
                db,
                user_id=sell_tx.user_id,
                asset_id=sell_tx.asset_id,
                before_date=sell_tx.transaction_date
            )

            remaining_qty = sell_tx.quantity
            for lot in available_lots:
                if remaining_qty <= 0:
                    break
                take_qty = min(lot["available_quantity"], remaining_qty)
                if take_qty > 0:
                    link = TransactionLink(
                        sell_transaction_id=sell_tx.id,
                        buy_transaction_id=lot["id"],
                        quantity=take_qty,
                    )
                    db.add(link)
                    remaining_qty -= take_qty
                    created_count += 1
                    logger.info(
                        f"  Created link: {take_qty} from lot {lot['id']} "
                        f"(date: {lot['date']})"
                    )

            if remaining_qty > 0:
                logger.warning(
                    f"  WARNING: Could not fully link SELL {sell_tx.id}. "
                    f"Remaining: {remaining_qty}"
                )

        db.commit()
        logger.info(f"Backfill complete. Created {created_count} TransactionLinks.")

    except Exception as e:
        db.rollback()
        logger.error(f"Backfill failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    backfill_links()
