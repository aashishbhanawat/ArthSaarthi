import logging
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
