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
    1. Saves the DIVIDEND transaction for auditing and income tracking.
    2. If the dividend is reinvested, creates a corresponding BUY transaction.
    """
    logger.info(f"Handling dividend for asset {asset_id} in portfolio {portfolio_id}")

    # Always save the dividend transaction itself for record-keeping.
    dividend_audit_transaction = crud.transaction.create_with_portfolio(
        db=db, obj_in=transaction_in, portfolio_id=portfolio_id
    )
    logger.info(f"Saved DIVIDEND audit transaction {dividend_audit_transaction.id}")

    if transaction_in.is_reinvested:
        logger.info("Dividend is marked for reinvestment.")
        # For reinvested dividends, the total dividend amount is in 'quantity'
        # and the reinvestment price is in 'price_per_unit'.
        # We need to calculate the number of shares purchased.
        reinvestment_price = transaction_in.price_per_unit
        total_dividend_amount = transaction_in.quantity

        if reinvestment_price <= 0:
            raise HTTPException(
                status_code=400,
                detail="Reinvestment price must be greater than zero.",
            )

        quantity_reinvested = total_dividend_amount / reinvestment_price
        logger.info(
            f"Calculated reinvestment quantity: {quantity_reinvested} shares at "
            f"price {reinvestment_price}"
        )

        reinvest_buy_in = schemas.TransactionCreate(
            asset_id=asset_id,
            transaction_type=TransactionType.BUY,
            quantity=quantity_reinvested,
            price_per_unit=reinvestment_price,
            transaction_date=transaction_in.transaction_date,
            fees=Decimal("0.0"),
            is_reinvested=True,  # Mark this BUY as part of a reinvestment
        )
        crud.transaction.create_with_portfolio(
            db=db, obj_in=reinvest_buy_in, portfolio_id=portfolio_id
        )
        logger.info("Created corresponding BUY transaction for reinvested dividend.")

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

    split_factor = split_ratio_new / split_ratio_old
    logger.info(f"Split factor calculated: {split_factor}")

    # Fetch all historical transactions for this asset in the portfolio
    transactions_to_adjust = (
        crud.transaction.get_multi_by_portfolio_and_asset_before_date(
            db,
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            date=transaction_in.transaction_date,
        )
    )

    logger.info(
        f"Found {len(transactions_to_adjust)} transactions to adjust for split."
    )

    for tx in transactions_to_adjust:
        original_quantity = tx.quantity
        original_price = tx.price_per_unit

        tx.quantity = original_quantity * split_factor
        tx.price_per_unit = original_price / split_factor
        db.add(tx)
        logger.info(
            f"Adjusted transaction {tx.id}: "
            f"qty {original_quantity} -> {tx.quantity}, "
            f"price {original_price} -> {tx.price_per_unit}"
        )

    # Save the SPLIT transaction itself for auditing
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