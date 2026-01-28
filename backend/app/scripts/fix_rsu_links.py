import logging
import sys

# Add app to path
sys.path.insert(0, "/app")


from app.db.session import SessionLocal
from app.models.transaction import Transaction
from app.models.transaction_link import TransactionLink
from app.schemas.enums import TransactionType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_rsu_links():
    db = SessionLocal()
    try:
        # Find all RSU_VEST transactions
        rsu_vests = db.query(Transaction).filter(
            Transaction.transaction_type == TransactionType.RSU_VEST
        ).all()

        logger.info(f"Found {len(rsu_vests)} RSU Vests.")

        fixed_count = 0

        for vest in rsu_vests:
            # Find candidate Sell-to-Cover transactions
            # Rules:
            # 1. Same Portfolio, Same Asset
            # 2. Same Date (approx? strict equality for date part)
            # 3. Transaction Type = SELL

            # Note: transaction_date is datetime. We compare date() part.
            vest_date = vest.transaction_date.date()

            # Query Sells
            sells = db.query(Transaction).filter(
                Transaction.portfolio_id == vest.portfolio_id,
                Transaction.asset_id == vest.asset_id,
                Transaction.transaction_type == TransactionType.SELL
            ).all()

            # Filter in python for date match
            # (easier than sqlalchemy cast across DB types)
            candidate_sells = [
                s for s in sells
                if s.transaction_date.date() == vest_date
            ]

            for sell in candidate_sells:
                logger.info(
                    f"Checking Sell {sell.id} (Qty: {sell.quantity}) "
                    f"on {vest_date} against RSU Vest {vest.id} (Qty: {vest.quantity})"
                )

                # Check existing links
                existing_links = db.query(TransactionLink).filter(
                    TransactionLink.sell_transaction_id == sell.id
                ).all()

                # Check if it is valid Sell to Cover?
                # Usually Sell Qty < Vest Qty.
                if sell.quantity > vest.quantity:
                    logger.warning(f"  Skipping: Sell Qty {sell.quantity} > Vest Qty {vest.quantity}. Unlikely to be purely Sell-to-Cover.")
                    continue

                # Check if ALREADY correctly linked
                fully_linked_to_vest = False
                if existing_links:
                    total_linked_to_vest = sum(l.quantity for l in existing_links if l.buy_transaction_id == vest.id)
                    total_linked_other = sum(l.quantity for l in existing_links if l.buy_transaction_id != vest.id)

                    if total_linked_to_vest == sell.quantity and total_linked_other == 0:
                        logger.info("  Already correctly linked.")
                        continue

                    if total_linked_other > 0:
                        logger.info(f"  Found links to OTHER lots ({total_linked_other}). Fixing...")

                        # DELETE existing links
                        for l in existing_links:
                            db.delete(l)
                        db.flush()
                else:
                    logger.info("  No existing links. Linking to RSU...")

                # Create proper link
                link = TransactionLink(
                    sell_transaction_id=sell.id,
                    buy_transaction_id=vest.id,
                    quantity=sell.quantity
                )
                db.add(link)
                fixed_count += 1
                logger.info("  Fixed Link.")

        db.commit()
        logger.info(f"Fix complete. Relinked {fixed_count} transactions.")

    except Exception as e:
        db.rollback()
        logger.error(f"Fix failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_rsu_links()
