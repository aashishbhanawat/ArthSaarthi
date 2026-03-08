import logging
import uuid
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Union

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import crud, schemas
from app.crud.base import CRUDBase
from app.models.transaction import Transaction
from app.models.transaction_link import TransactionLink
from app.schemas.enums import TransactionType
from app.schemas.transaction import TransactionCreate, TransactionUpdate

logger = logging.getLogger(__name__)


class CRUDTransaction(CRUDBase[Transaction, TransactionCreate, TransactionUpdate]):
    def get_holdings_on_date(
        self, db: Session, *, user_id: uuid.UUID, asset_id: uuid.UUID, on_date: datetime
    ) -> Decimal:
        # Fetch all relevant transactions sorted by date
        transactions = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.asset_id == asset_id,
                Transaction.transaction_date <= on_date,
            )
            .order_by(Transaction.transaction_date)
            .all()
        )

        units = Decimal("0")

        for tx in transactions:
            ttype = tx.transaction_type
            qty = tx.quantity

            if ttype in [
                TransactionType.BUY,
                TransactionType.ESPP_PURCHASE,
                TransactionType.RSU_VEST,
                # TransactionType.BONUS - Excluded as it is an audit record;
                # actual shares are in a BUY tx
                TransactionType.CONTRIBUTION
            ]:
                units += qty
            elif ttype == TransactionType.SELL:
                units -= qty
            elif ttype == TransactionType.SPLIT:
                # Split logic: multiplier = new_ratio / old_ratio
                # quantity = new, price_per_unit = old
                if tx.price_per_unit and tx.price_per_unit > 0:
                    multiplier = tx.quantity / tx.price_per_unit
                    units = units * multiplier
            # Merger/Demerger/Rename usually effectively close position or open new
            # assets, but strict holding count logic might need fine tuning
            # if we wanted to prevent selling "old" merged shares.
            # For now, SPLIT is the primary in-place modifier.

        return units

    def get_cost_basis_on_date(
        self, db: Session, *, user_id: uuid.UUID, asset_id: uuid.UUID, on_date: datetime
    ) -> Decimal:
        """
        Calculate total cost basis for an asset up to a given date.
        Cost basis = sum of (quantity * price_per_unit) for all
        acquisition transactions. Used by merger/demerger handlers.
        """
        acquisition_types = ["BUY", "ESPP_PURCHASE", "RSU_VEST"]
        # Sum of (quantity * price_per_unit) for all acquisitions
        result = db.query(
            func.sum(Transaction.quantity * Transaction.price_per_unit)
        ).filter(
            Transaction.user_id == user_id,
            Transaction.asset_id == asset_id,
            Transaction.transaction_type.in_(acquisition_types),
            Transaction.transaction_date <= on_date,
        ).scalar() or Decimal("0")

        return Decimal(str(result))

    # The create_with_portfolio method is now simplified.
    # The complex logic for creating a new asset is removed.
    def create_with_portfolio(
        self,
        db: Session,
        *,
        obj_in: schemas.TransactionCreate,
        portfolio_id: uuid.UUID,
    ) -> Union[Transaction, List[Transaction]]:
        logger.debug(
            f"Entering create_with_portfolio for type: {obj_in.transaction_type}"
        )

        # --- Idempotency Check for the main transaction ---
        # To prevent duplicate submissions from the frontend, check if a very
        # similar transaction was created recently.
        # This is particularly for the RSU/ESPP flow.
        if obj_in.transaction_type in [
            TransactionType.RSU_VEST,
            TransactionType.ESPP_PURCHASE,
        ]:
            logger.debug(
                f"idempotency check for {obj_in.transaction_type} transaction."
            )
            existing_tx = self.get_by_details(
                db,
                portfolio_id=portfolio_id,
                asset_id=obj_in.asset_id,
                transaction_date=obj_in.transaction_date,
                transaction_type=obj_in.transaction_type,
                quantity=obj_in.quantity,
                price_per_unit=obj_in.price_per_unit,
            )
            if existing_tx:
                logger.warning(
                    f"An identical {obj_in.transaction_type} transaction already "
                    f"exists (ID: {existing_tx.id}). Skipping creation of duplicate."
                )
                return existing_tx

        portfolio = crud.portfolio.get(db=db, id=portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # Check for sufficient holdings only for standalone SELL transactions.
        # This check is skipped for 'Sell to Cover' which is created atomically
        # with its parent RSU Vest.
        is_sell_to_cover = obj_in.details and "related_rsu_vest_id" in obj_in.details
        if obj_in.transaction_type.upper() == "SELL" and not is_sell_to_cover:
            current_holdings = self.get_holdings_on_date(
                db,
                user_id=portfolio.user_id,
                asset_id=obj_in.asset_id,
                on_date=obj_in.transaction_date,
            )
            logger.debug(
                f"Checking holdings for SELL. Current: {current_holdings}, "
                f"Attempting to sell: {obj_in.quantity}"
            )
            # Use a small epsilon for float comparison if needed, but Decimal is exact
            if obj_in.quantity > current_holdings:
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Insufficient holdings to sell. Current holdings:"
                        f" {current_holdings}, trying to sell: {obj_in.quantity}"
                    ),
                )

        db_obj = self.model(
            **obj_in.model_dump(exclude={"links"}),
            user_id=portfolio.user_id,
            portfolio_id=portfolio_id,
        )
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)

        if obj_in.links:
            for link_data in obj_in.links:
                link = TransactionLink(
                    sell_transaction_id=db_obj.id,
                    buy_transaction_id=link_data.buy_transaction_id,
                    quantity=link_data.quantity,
                )
                db.add(link)
            db.flush()
            db.refresh(db_obj)
        elif obj_in.transaction_type.upper() == "SELL":
            # --- Auto-FIFO Linking ---
            # If no explicit links provided, automatically create links using FIFO.
            logger.debug(
                f"Auto-FIFO linking for SELL tx {db_obj.id}, qty: {obj_in.quantity}"
            )
            available_lots = self.get_available_lots(
                db=db, user_id=portfolio.user_id, asset_id=obj_in.asset_id,
                exclude_sell_id=db_obj.id
            )
            remaining_qty = obj_in.quantity
            for lot in available_lots:
                if remaining_qty <= 0:
                    break
                take_qty = min(lot["available_quantity"], remaining_qty)
                if take_qty > 0:
                    link = TransactionLink(
                        sell_transaction_id=db_obj.id,
                        buy_transaction_id=lot["id"],
                        quantity=take_qty,
                    )
                    db.add(link)
                    remaining_qty -= take_qty
                    logger.debug(
                        f"  Linked {take_qty} from lot {lot['id']} "
                        f"(date: {lot['date']})"
                    )
            if remaining_qty > 0:
                logger.warning(
                    f"Auto-FIFO: Could not fully link SELL tx {db_obj.id}. "
                    f"Remaining: {remaining_qty}"
                )
            db.flush()
            db.refresh(db_obj)

        # --- Handle "Sell to Cover" for RSU Vest ---
        # If the transaction is an RSU vest and has sell_to_cover details,
        # create a corresponding SELL transaction.
        logger.debug(
            "Checking for sell_to_cover. Type: %s, Details: %s",
            db_obj.transaction_type,
            db_obj.details,
        )
        if (
            db_obj.transaction_type == TransactionType.RSU_VEST
            and db_obj.details
            and "sell_to_cover" in db_obj.details
        ):
            logger.debug(
                "RSU_VEST with sell_to_cover found. Creating SELL transaction."
            )
            sell_details = db_obj.details["sell_to_cover"]
            sell_quantity = Decimal(str(sell_details.get("quantity", 0)))

            if sell_quantity > 0:
                # --- Idempotency Check ---
                # Check if a SELL transaction for this RSU vest already exists.
                existing_sell = db.query(Transaction).filter(
                    Transaction.portfolio_id == portfolio_id,
                    Transaction.transaction_type == TransactionType.SELL,
                    Transaction.details.op("->>")("related_rsu_vest_id")
                    == str(db_obj.id),
                ).first()

                if existing_sell:
                    logger.warning(
                        "A 'Sell to Cover' transaction for RSU Vest ID %s already "
                        "exists. Skipping creation of duplicate.",
                        db_obj.id,
                    )
                    return [db_obj, existing_sell]

                logger.debug(
                    "Sell quantity > 0 (%s). Proceeding with recursive call.",
                    sell_quantity,
                )
                # Create the SELL transaction
                sell_transaction_in = schemas.TransactionCreate(
                    asset_id=db_obj.asset_id,
                    transaction_type=TransactionType.SELL,
                    quantity=sell_quantity,
                    price_per_unit=Decimal(str(sell_details.get("price_per_unit", 0))),
                    transaction_date=db_obj.transaction_date,
                    details={
                        "fx_rate": db_obj.details.get("fx_rate"),
                        "related_rsu_vest_id": str(db_obj.id),
                    },
                    links=[
                        schemas.TransactionLinkCreate(
                            buy_transaction_id=db_obj.id,
                            quantity=sell_quantity
                        )
                    ]
                )
                # Recursively call create_with_portfolio for the SELL transaction
                logger.debug(
                    "calling create_with_portfolio for SELL transaction recusively."
                )
                logger.debug(f"sell_transaction_in: {sell_transaction_in}")
                sell_tx = self.create_with_portfolio(
                    db,
                    obj_in=sell_transaction_in,
                    portfolio_id=portfolio_id,
                )
                return [db_obj, sell_tx]
                logger.debug("Done with recursive call.")
            else:
                logger.debug("Sell quantity is 0. Skipping SELL transaction creation.")
        else:
            logger.debug("Condition for sell_to_cover not met. No recursive call.")

        return db_obj

    def get_multi_by_user_with_filters(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        portfolio_id: uuid.UUID,
        asset_id: Optional[uuid.UUID] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Transaction], int]:
        query = db.query(self.model).filter(
            self.model.user_id == user_id, self.model.portfolio_id == portfolio_id
        )

        if asset_id:
            query = query.filter(self.model.asset_id == asset_id)
        if transaction_type:
            query = query.filter(
                self.model.transaction_type == transaction_type.upper()
            )
        if start_date:
            query = query.filter(self.model.transaction_date >= start_date)
        if end_date:
            query = query.filter(self.model.transaction_date <= end_date)

        total = query.count()
        transactions = (
            query.order_by(self.model.transaction_date.desc()).offset(skip).limit(limit).all()
        )
        return transactions, total

    def get_multi_by_portfolio(
        self, db: Session, *, portfolio_id: uuid.UUID
    ) -> List[Transaction]:
        return (
            db.query(self.model).filter(self.model.portfolio_id == portfolio_id).all()
        )

    def get_multi_by_asset(
        self, db: Session, *, asset_id: uuid.UUID
    ) -> List[Transaction]:
        """Retrieves all transactions for a specific asset."""
        return db.query(self.model).filter(self.model.asset_id == asset_id).all()

    def get_multi_by_portfolio_and_asset(
        self, db: Session, *, portfolio_id: uuid.UUID, asset_id: uuid.UUID
    ) -> List[Transaction]:
        return (
            db.query(self.model)
            .filter(
                Transaction.portfolio_id == portfolio_id,
                Transaction.asset_id == asset_id,
            )
            .order_by(Transaction.transaction_date)
            .all()
        )

    def get_multi_by_portfolio_and_asset_before_date(
        self,
        db: Session,
        *,
        portfolio_id: uuid.UUID,
        asset_id: uuid.UUID,
        date: datetime,
    ) -> List[Transaction]:
        """
        Retrieves all BUY and SELL transactions for a specific asset in a portfolio
        that occurred before a given date.
        """
        return (
            db.query(self.model)
            .filter(
                Transaction.portfolio_id == portfolio_id,
                Transaction.asset_id == asset_id,
                Transaction.transaction_date < date,
                Transaction.transaction_type.in_(["BUY", "SELL"]),
            )
            .order_by(Transaction.transaction_date)
            .all()
        )

    def get_by_details(
        self,
        db: Session,
        *,
        portfolio_id: uuid.UUID,
        asset_id: uuid.UUID,
        transaction_date: datetime,
        transaction_type: str,
        quantity: Decimal,
        price_per_unit: Decimal,
    ) -> Transaction | None:
        # Allow small tolerance for price_per_unit (0.5%) to handle NAV precision
        # differences between different parsers (e.g., KFintech vs CAMS)
        price_tolerance = price_per_unit * Decimal("0.005")  # 0.5% tolerance
        price_low = price_per_unit - price_tolerance
        price_high = price_per_unit + price_tolerance

        # Also allow small tolerance for quantity (0.1%) for rounding differences
        qty_tolerance = quantity * Decimal("0.001")  # 0.1% tolerance
        qty_low = quantity - qty_tolerance
        qty_high = quantity + qty_tolerance

        return (
            db.query(self.model)
            .filter(
                self.model.portfolio_id == portfolio_id,
                self.model.asset_id == asset_id,
                self.model.transaction_date == transaction_date,
                self.model.transaction_type == transaction_type,
                self.model.quantity >= qty_low,
                self.model.quantity <= qty_high,
                self.model.price_per_unit >= price_low,
                self.model.price_per_unit <= price_high,
            )
            .first()
        )


    def get_available_lots(
        self, db: Session, *, user_id: uuid.UUID, asset_id: uuid.UUID,
        exclude_sell_id: Optional[uuid.UUID] = None
    ) -> List[dict]:
        """
        Calculates available lots for an asset using FIFO matching for unlinked sells
        and specific identification for linked sells.

        Args:
            exclude_sell_id: Optional SELL transaction ID to exclude from processing
                            (used during auto-linking to avoid the new SELL
                            consuming its own lots)
        """
        # Fetch all relevant transactions sorted by date
        transactions = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.asset_id == asset_id,
                Transaction.transaction_type.in_(
                    ["BUY", "ESPP_PURCHASE", "RSU_VEST", "SELL"]
                ),
            )
            .order_by(Transaction.transaction_date)
            .all()
        )

        # Sort by date, then by type priority (Acquisitions BEFORE Disposals)
        # This ensures that if RSU Vest and Sell-to-Cover share the exact same
        # timestamp, the Vest is processed first so the lot exists for the Sell
        # to consume.
        def get_type_priority(tx_type: str) -> int:
            if tx_type in ["BUY", "ESPP_PURCHASE", "RSU_VEST"]:
                return 1
            if tx_type == "SELL":
                return 2
            return 3

        transactions.sort(key=lambda t: (
            t.transaction_date, get_type_priority(t.transaction_type)
        ))

        # --- Pre-fetch Transaction Links (Avoid N+1 Queries) ---
        # Identify all relevant SELL transactions to batch-fetch their links.
        sell_tx_ids = [
            tx.id
            for tx in transactions
            if tx.transaction_type == "SELL"
            and (not exclude_sell_id or tx.id != exclude_sell_id)
        ]

        links_map = defaultdict(list)
        if sell_tx_ids:
            all_links = (
                db.query(TransactionLink)
                .filter(TransactionLink.sell_transaction_id.in_(sell_tx_ids))
                .all()
            )
            for link in all_links:
                links_map[link.sell_transaction_id].append(link)

        lots = []  # List of buys: {tx, available_quantity}

        for tx in transactions:
            if tx.transaction_type in ["BUY", "ESPP_PURCHASE", "RSU_VEST"]:
                lots.append(
                    {
                        "transaction": tx,
                        "available_quantity": tx.quantity,
                        "date": tx.transaction_date,
                    }
                )
            elif tx.transaction_type == "SELL":
                # Skip the excluded sell (used during auto-linking)
                if exclude_sell_id and tx.id == exclude_sell_id:
                    continue
                sell_qty = tx.quantity

                # 1. Process Specific Links
                # Use pre-fetched links from map
                links = links_map.get(tx.id, [])

                linked_buy_ids = {}
                for link in links:
                    linked_buy_ids[link.buy_transaction_id] = link.quantity
                    sell_qty -= link.quantity

                    # Deduct from the specific lot
                    for lot in lots:
                        if lot["transaction"].id == link.buy_transaction_id:
                            lot["available_quantity"] -= link.quantity
                            break

                # 2. Process Remaining Quantity (Unlinked) via FIFO
                if sell_qty > 0:
                    for lot in lots:
                        if lot["available_quantity"] > 0:
                            take = min(lot["available_quantity"], sell_qty)
                            lot["available_quantity"] -= take
                            sell_qty -= take
                            if sell_qty <= 0:
                                break

        # Filter out fully consumed lots
        available_lots = [
            {
                "id": lot["transaction"].id,
                "date": lot["date"],
                "available_quantity": lot["available_quantity"],
                "price_per_unit": lot["transaction"].price_per_unit,
                "type": lot["transaction"].transaction_type,
                "details": lot["transaction"].details
            }
            for lot in lots
            if lot["available_quantity"] > 0
        ]

        return available_lots


transaction = CRUDTransaction(Transaction)
