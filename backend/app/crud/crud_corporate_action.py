import logging
import math
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.schemas.enums import TransactionType

logger = logging.getLogger(__name__)


def handle_dividend(
    db: Session,
    *,
    portfolio_id: UUID,
    asset_id: UUID,
    transaction_in: schemas.TransactionCreate,
) -> models.Transaction:
    """
    Handles a dividend corporate action.
    Saves the DIVIDEND transaction for auditing and income tracking.
    If the dividend is marked as reinvested, it also creates a corresponding BUY
    transaction.
    """
    logger.info(
        f"Handling dividend for asset {asset_id} in portfolio {portfolio_id}. "
        f"Is Reinvested: {getattr(transaction_in, 'is_reinvested', False)}"
    )
    logger.debug("Payload received by handle_dividend: %s",
                 transaction_in.model_dump_json(indent=2))

    # Always save the dividend transaction itself for record-keeping.
    # We create a new schema here to ensure only relevant fields are passed.
    dividend_audit_schema = schemas.TransactionCreate(
        asset_id=asset_id,
        transaction_type=TransactionType.DIVIDEND,
        quantity=transaction_in.quantity,
        price_per_unit=transaction_in.price_per_unit,
        transaction_date=transaction_in.transaction_date,
        fees=getattr(transaction_in, "fees", 0),
    )
    dividend_audit_transaction = crud.transaction.create_with_portfolio(
        db=db, obj_in=dividend_audit_schema, portfolio_id=portfolio_id
    )
    logger.info(f"Saved DIVIDEND audit transaction {dividend_audit_transaction.id}")

    # If reinvested, create a corresponding BUY transaction
    if getattr(transaction_in, "is_reinvested", False) is True:
        logger.info(
            "Dividend is marked as reinvested. Proceeding to create BUY transaction."
        )
        reinvestment_nav = getattr(transaction_in, "reinvestment_nav", None)
        logger.debug(f"Reinvestment NAV: {reinvestment_nav}")
        logger.debug(
            "Dividend Amount (from transaction_in.quantity): %s",
            transaction_in.quantity,
        )

        if not reinvestment_nav or reinvestment_nav <= 0:
            logger.error(
                "Reinvestment NAV is missing or invalid. "
                "Aborting BUY transaction creation."
            )
            raise HTTPException(
                status_code=400, detail="NAV is required for reinvestment."
            )

        reinvested_quantity = transaction_in.quantity / reinvestment_nav
        logger.info(f"Calculated reinvested quantity: {reinvested_quantity}")

        buy_transaction_schema = schemas.TransactionCreate(
            asset_id=asset_id,
            transaction_type=TransactionType.BUY,
            quantity=reinvested_quantity,
            price_per_unit=reinvestment_nav,
            transaction_date=transaction_in.transaction_date,
        )
        crud.transaction.create_with_portfolio(
            db=db, obj_in=buy_transaction_schema, portfolio_id=portfolio_id
        )
        logger.info(
            "Saved corresponding BUY transaction for reinvested dividend."
        )
    else:
        logger.info(
            "Dividend is not marked as reinvested. Skipping BUY transaction creation."
        )

    return dividend_audit_transaction


def handle_stock_split(
    db: Session,
    *,
    portfolio_id: UUID,
    asset_id: UUID,
    transaction_in: schemas.TransactionCreate,
) -> models.Transaction:
    """
    Handles a stock split corporate action.
    1. Fetches all BUY/SELL transactions for the asset before the split date.
    2. Adjusts the quantity and price for each transaction based on the ratio.
    3. Saves the SPLIT transaction itself for auditing.
    """
    logger.info(
        f"Handling stock split for asset {asset_id} in portfolio {portfolio_id}"
    )

    split_ratio_new = transaction_in.quantity
    split_ratio_old = transaction_in.price_per_unit

    if split_ratio_old <= 0 or split_ratio_new <= 0:
        raise HTTPException(status_code=400, detail="Invalid split ratio.")

    # Create the SPLIT transaction for auditing/event-sourcing
    # We DO NOT mutate historical transactions anymore.
    # The holdings calculation logic (crud_holding.py) parses this SPLIT transaction
    # and effectively "replays" the split to adjust quantity/cost basis at runtime.
    # This preserves the historical truth of the original BUY transactions.

    split_audit_transaction = crud.transaction.create_with_portfolio(
        db=db, obj_in=transaction_in, portfolio_id=portfolio_id
    )
    logger.info("Saved SPLIT audit transaction.")

    return split_audit_transaction


def handle_bonus_issue(
    db: Session,
    *,
    portfolio_id: UUID,
    asset_id: UUID,
    transaction_in: schemas.TransactionCreate,
) -> models.Transaction:
    """
    Handles a bonus issue corporate action.
    1. Calculates the net holdings of the asset on the effective date.
    2. Calculates the number of bonus shares to be issued.
    3. Creates a new BUY transaction for the bonus shares with a price of 0.
    4. Saves the original BONUS transaction for auditing.
    """
    logger.info(
        f"Handling bonus issue for asset {asset_id} in portfolio {portfolio_id}"
    )

    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    net_holdings = crud.transaction.get_holdings_on_date(
        db,
        user_id=portfolio.user_id,
        asset_id=asset_id,
        on_date=transaction_in.transaction_date,
    )

    if net_holdings <= 0:
        logger.warning(
            "Bonus issue for asset %s not processed as there were no holdings on %s",
            asset_id,
            transaction_in.transaction_date,
        )
        # Still save the BONUS transaction for audit, but don't create a BUY
        return crud.transaction.create_with_portfolio(
            db=db, obj_in=transaction_in, portfolio_id=portfolio_id
        )

    # For BONUS: quantity = new shares, price_per_unit = old shares
    new_shares_ratio = transaction_in.quantity
    old_shares_ratio = transaction_in.price_per_unit

    if old_shares_ratio <= 0:
        raise HTTPException(status_code=400, detail="Invalid bonus ratio.")

    bonus_shares_to_issue = (net_holdings / old_shares_ratio) * new_shares_ratio
    logger.info(f"Calculated bonus shares to issue: {bonus_shares_to_issue}")

    # For Indian stocks, fractional shares are not issued.
    # Truncate to the nearest lower integer (floor).
    asset = crud.asset.get(db, id=asset_id)
    if asset and asset.currency == "INR":
        bonus_shares_to_issue = Decimal(math.floor(bonus_shares_to_issue))
        logger.info(f"Asset is INR. Floored bonus shares to: {bonus_shares_to_issue}")

    if bonus_shares_to_issue > 0:
        bonus_buy_transaction_in = schemas.TransactionCreate(
            asset_id=asset_id,
            transaction_type=TransactionType.BUY,
            quantity=bonus_shares_to_issue,
            price_per_unit=Decimal("0.0"),  # Bonus shares have zero cost
            transaction_date=transaction_in.transaction_date,
            fees=Decimal("0.0"),
        )
        crud.transaction.create_with_portfolio(
            db=db, obj_in=bonus_buy_transaction_in, portfolio_id=portfolio_id
        )
        logger.info(
            "Created zero-cost BUY transaction for %s bonus shares.",
            bonus_shares_to_issue,
        )

    # Save the original BONUS transaction for auditing purposes
    bonus_audit_transaction = crud.transaction.create_with_portfolio(
        db=db, obj_in=transaction_in, portfolio_id=portfolio_id
    )
    logger.info("Saved BONUS audit transaction.")

    return bonus_audit_transaction


def handle_merger(
    db: Session,
    *,
    portfolio_id: UUID,
    asset_id: UUID,
    transaction_in: schemas.TransactionCreate,
) -> models.Transaction:
    """
    Handles a stock merger (amalgamation) corporate action.

    Tax Treatment (India - Section 47(vii)):
    - Share exchange is NOT a "transfer" for capital gains purposes
    - Original cost basis and acquisition dates are preserved
    - Capital gains arise only upon eventual sale of new shares

    Process:
    1. Saves MERGER audit transaction with full details in JSON
    2. Creates BUY transaction for new shares preserving cost basis
    3. Holdings calculation will interpret MERGER to hide old holdings
    """
    logger.info(
        f"Handling merger for asset {asset_id} in portfolio {portfolio_id}"
    )

    details = transaction_in.details or {}
    record_date = transaction_in.transaction_date
    conversion_ratio = transaction_in.quantity  # New shares per old share
    new_asset_id = details.get("new_asset_id")
    new_asset_ticker = details.get("new_asset_ticker")

    # Resolve new asset - accept either ID or ticker
    if not new_asset_id and not new_asset_ticker:
        raise HTTPException(
            status_code=400,
            detail="new_asset_id or new_asset_ticker is required in details for merger"
        )

    if not new_asset_id and new_asset_ticker:
        # Look up or create the new asset by ticker
        new_asset = crud.asset.get_or_create_by_ticker(
            db, ticker_symbol=new_asset_ticker, asset_type="STOCK"
        )
        new_asset_id = str(new_asset.id)

    if conversion_ratio <= 0:
        raise HTTPException(status_code=400, detail="Invalid conversion ratio.")

    # Get the portfolio to access user_id
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Calculate current holdings of the old asset
    old_holdings = crud.transaction.get_holdings_on_date(
        db,
        user_id=portfolio.user_id,
        asset_id=asset_id,
        on_date=record_date,
    )

    if old_holdings <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"No holdings found for this asset on {record_date}"
        )

    # Calculate new shares based on conversion ratio
    new_shares = old_holdings * conversion_ratio
    logger.info(f"Converting {old_holdings} old shares to {new_shares} new shares")

    # Fetch original BUY transactions to preserve acquisition dates
    # This is critical for correct XIRR and holding period calculation
    original_buys = db.query(models.Transaction).filter(
        models.Transaction.portfolio_id == portfolio_id,
        models.Transaction.asset_id == asset_id,
        models.Transaction.transaction_type.in_(["BUY", "ESPP_PURCHASE", "RSU_VEST"]),
        models.Transaction.transaction_date <= record_date,
    ).all()

    # Create BUY transactions for new asset preserving original acquisition dates
    for orig_buy in original_buys:
        # Adjust quantity by conversion ratio
        new_qty = orig_buy.quantity * conversion_ratio
        # Adjust price inversely to preserve total cost basis
        # (new_qty * new_price = orig_qty * orig_price)
        adjusted_price = orig_buy.price_per_unit / conversion_ratio
        new_share_buy = schemas.TransactionCreate(
            asset_id=UUID(new_asset_id),
            transaction_type=TransactionType.BUY,
            quantity=new_qty,
            price_per_unit=adjusted_price,
            transaction_date=orig_buy.transaction_date,  # Preserve original date!
            fees=Decimal("0.0"),
            details={
                "from_merger": True,
                "original_asset_id": str(asset_id),
                "original_transaction_id": str(orig_buy.id),
            },
        )
        crud.transaction.create_with_portfolio(
            db=db, obj_in=new_share_buy, portfolio_id=portfolio_id
        )
        logger.info(
            f"Created BUY for {new_qty} shares, date {orig_buy.transaction_date}"
        )

    # Save the MERGER audit transaction
    merger_audit = crud.transaction.create_with_portfolio(
        db=db, obj_in=transaction_in, portfolio_id=portfolio_id
    )
    logger.info("Saved MERGER audit transaction.")

    return merger_audit


def handle_demerger(
    db: Session,
    *,
    portfolio_id: UUID,
    asset_id: UUID,
    transaction_in: schemas.TransactionCreate,
) -> models.Transaction:
    """
    Handles a stock demerger (spin-off) corporate action.

    Process:
    1. Keeps original holding (cost basis may be reduced)
    2. Creates BUY transactions for demerged shares with proportional cost basis
    3. Preserves original acquisition dates for holding period
    """
    logger.info(
        f"Handling demerger for asset {asset_id} in portfolio {portfolio_id}"
    )

    details = transaction_in.details or {}
    record_date = transaction_in.transaction_date
    new_asset_id = details.get("new_asset_id")
    new_asset_ticker = details.get("new_asset_ticker")
    ratio = transaction_in.quantity  # New shares per old share
    cost_allocation_pct = Decimal(str(details.get("cost_allocation_pct", "0")))

    # Resolve new asset - accept either ID or ticker
    if not new_asset_id and not new_asset_ticker:
        raise HTTPException(
            status_code=400,
            detail="new_asset_id or new_asset_ticker required for demerger"
        )

    if not new_asset_id and new_asset_ticker:
        new_asset = crud.asset.get_or_create_by_ticker(
            db, ticker_symbol=new_asset_ticker, asset_type="STOCK"
        )
        new_asset_id = str(new_asset.id)

    if ratio <= 0:
        raise HTTPException(status_code=400, detail="Invalid demerger ratio.")

    # Get the portfolio
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Calculate current holdings
    old_holdings = crud.transaction.get_holdings_on_date(
        db,
        user_id=portfolio.user_id,
        asset_id=asset_id,
        on_date=record_date,
    )

    if old_holdings <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"No holdings found for this asset on {record_date}"
        )

    # Calculate demerged shares
    demerged_shares = old_holdings * ratio
    logger.info(f"Demerging {demerged_shares} shares from {old_holdings}")

    # Fetch original BUY transactions to preserve acquisition dates
    # This is critical for correct XIRR and holding period calculation
    original_buys = db.query(models.Transaction).filter(
        models.Transaction.portfolio_id == portfolio_id,
        models.Transaction.asset_id == asset_id,
        models.Transaction.transaction_type.in_(["BUY", "ESPP_PURCHASE", "RSU_VEST"]),
        models.Transaction.transaction_date <= record_date,
    ).all()

    # Calculate total cost being allocated to child (for holdings reduction)
    total_cost_allocated = Decimal("0.0")
    pct = cost_allocation_pct / Decimal("100")

    # Create BUY transactions for demerged child shares only
    for orig_buy in original_buys:
        # Adjust quantity by ratio for child
        new_qty = orig_buy.quantity * ratio
        # Adjusted price = (total cost allocated to child) / (child shares)
        # = (orig_price * pct) / ratio
        # This ensures: new_qty * adjusted_price = orig_qty * orig_price * pct
        adjusted_price = orig_buy.price_per_unit * pct / Decimal(str(ratio))
        # Track total cost allocated
        total_cost_allocated += orig_buy.quantity * orig_buy.price_per_unit * pct

        # Create child BUY
        demerged_buy = schemas.TransactionCreate(
            asset_id=UUID(new_asset_id),
            transaction_type=TransactionType.BUY,
            quantity=new_qty,
            price_per_unit=adjusted_price,
            transaction_date=orig_buy.transaction_date,
            fees=Decimal("0.0"),
            details={
                "from_demerger": True,
                "original_asset_id": str(asset_id),
                "original_transaction_id": str(orig_buy.id),
            },
        )
        crud.transaction.create_with_portfolio(
            db=db, obj_in=demerged_buy, portfolio_id=portfolio_id
        )
        logger.info(f"Created child BUY: {new_qty} @ {adjusted_price}")

    # Add metadata to the DEMERGER audit transaction
    updated_details = dict(transaction_in.details or {})
    updated_details["total_cost_allocated"] = str(total_cost_allocated)
    transaction_in_with_cost = transaction_in.model_copy(
        update={"details": updated_details}
    )

    # Save the DEMERGER audit transaction with cost info
    demerger_audit = crud.transaction.create_with_portfolio(
        db=db, obj_in=transaction_in_with_cost, portfolio_id=portfolio_id
    )
    logger.info(f"Saved DEMERGER. Cost allocated: {total_cost_allocated}")

    return demerger_audit


def handle_rename(
    db: Session,
    *,
    portfolio_id: UUID,
    asset_id: UUID,
    transaction_in: schemas.TransactionCreate,
) -> models.Transaction:
    """
    Handles a ticker rename/symbol change corporate action.

    Process:
    1. Creates RENAME audit transaction with mapping details
    2. Holdings calculation interprets RENAME to map old ticker to new
    3. No cost basis or holding period changes
    """
    logger.info(
        f"Handling rename for asset {asset_id} in portfolio {portfolio_id}"
    )

    details = transaction_in.details or {}
    new_asset_id = details.get("new_asset_id")
    new_asset_ticker = details.get("new_asset_ticker")

    # Resolve new asset - accept either ID or ticker
    if not new_asset_id and not new_asset_ticker:
        raise HTTPException(
            status_code=400,
            detail="new_asset_id or new_asset_ticker is required in details for rename"
        )

    if not new_asset_id and new_asset_ticker:
        new_asset = crud.asset.get_or_create_by_ticker(
            db, ticker_symbol=new_asset_ticker, asset_type="STOCK"
        )
        new_asset_id = str(new_asset.id)

    # Get the portfolio
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Get current holdings to transfer
    record_date = transaction_in.transaction_date
    old_holdings = crud.transaction.get_holdings_on_date(
        db,
        user_id=portfolio.user_id,
        asset_id=asset_id,
        on_date=record_date,
    )

    if old_holdings <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"No holdings found for this asset on {record_date}"
        )

    # Fetch original BUY transactions to preserve acquisition dates
    # This is critical for correct XIRR and holding period calculation
    original_buys = db.query(models.Transaction).filter(
        models.Transaction.portfolio_id == portfolio_id,
        models.Transaction.asset_id == asset_id,
        models.Transaction.transaction_type.in_(["BUY", "ESPP_PURCHASE", "RSU_VEST"]),
        models.Transaction.transaction_date <= record_date,
    ).all()

    # Create BUY transactions for new ticker preserving original acquisition dates
    for orig_buy in original_buys:
        new_ticker_buy = schemas.TransactionCreate(
            asset_id=UUID(new_asset_id),
            transaction_type=TransactionType.BUY,
            quantity=orig_buy.quantity,  # Same quantity for rename
            price_per_unit=orig_buy.price_per_unit,
            transaction_date=orig_buy.transaction_date,  # Preserve original date!
            fees=Decimal("0.0"),
            details={
                "from_rename": True,
                "original_asset_id": str(asset_id),
                "original_transaction_id": str(orig_buy.id),
            },
        )
        crud.transaction.create_with_portfolio(
            db=db, obj_in=new_ticker_buy, portfolio_id=portfolio_id
        )
        qty = orig_buy.quantity
        dt = orig_buy.transaction_date
        logger.info(f"Rename BUY: {qty} @ {dt}")

    # Save the RENAME audit transaction
    rename_audit = crud.transaction.create_with_portfolio(
        db=db, obj_in=transaction_in, portfolio_id=portfolio_id
    )
    logger.info("Saved RENAME audit transaction.")

    return rename_audit
