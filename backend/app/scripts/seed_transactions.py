import logging
import random
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app import crud, models, schemas
from app.db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_transactions(db: Session) -> None:
    """
    Seeds the database with sample portfolios and transactions for existing users.
    """
    logger.info("--- Starting to seed transaction data ---")

    # 1. Get the first user from the database (usually the admin)
    user = db.query(models.user.User).first()
    if not user:
        logger.error("No users found in the database. Please create an admin user first.")
        return
    logger.info(f"Found user: {user.email}. Seeding data for this user.")

    # 2. Define assets and ensure they exist in the DB
    tickers =  ["GHCL", "INFY", "ITC", "HAL", "ABB", "HDFCBANK", "ONGC", "NTPC", "SUNPHARMA", "HINDALCO", "BEML", "NBCC", "SBICARD"]
    assets = {}
    for ticker in tickers:
        asset = crud.asset.get_by_ticker(db, ticker_symbol=ticker)
        if not asset:
            logger.info(f"Asset {ticker} not found, creating it...")
            asset_in = schemas.AssetCreate(
                ticker_symbol=ticker,
                name=f"Placeholder for {ticker}",
                type="Crypto" if "-INR" in ticker else "Stock",
                currency="INR",
                exchange="CRYPTO" if "-USD" in ticker else "NSE",
            )
            asset = crud.asset.create(db=db, obj_in=asset_in)
            db.commit() # Commit after creating a new asset
        assets[ticker] = asset
    logger.info("Assets are ready.")

    # 3. Get or create a portfolio for the user
    portfolio_name = f"{user.full_name}'s Seeded Portfolio"
    portfolios = crud.portfolio.get_multi_by_owner(db=db, user_id=user.id)
    portfolio = next((p for p in portfolios if p.name == portfolio_name), None)
    if not portfolio:
        logger.info(f"Creating portfolio '{portfolio_name}' for user {user.email}")
        portfolio_in = schemas.PortfolioCreate(name=portfolio_name, description="Portfolio with auto-seeded sample data.")
        portfolio = crud.portfolio.create_with_owner(db=db, obj_in=portfolio_in, user_id=user.id)
        db.commit() # Commit after creating a new portfolio
    else:
        logger.info(f"Using existing portfolio '{portfolio_name}'")

    # 4. Seed transactions
    holdings = {}
    start_date = datetime.now() - timedelta(days=365 * 2)
    transactions_to_create = 50
    logger.info(f"Creating {transactions_to_create} new transactions...")

    for i in range(transactions_to_create):
        ticker = random.choice(tickers)
        asset_id = assets[ticker].id

        # If we don't hold it, we must buy. Otherwise, 70% chance to buy more.
        is_buy = holdings.get(ticker, 0) == 0 or random.random() < 0.7

        tx_date = start_date + timedelta(days=random.randint(0, 365 * 2))
        quantity = Decimal(random.randint(1, 20))
        price = Decimal(random.uniform(100, 500)).quantize(Decimal("0.01"))

        if is_buy:
            tx_in = schemas.TransactionCreate(
                asset_id=asset_id,
                transaction_type="BUY",
                quantity=quantity,
                price_per_unit=price,
                transaction_date=tx_date.date(),
            )
            crud.transaction.create_with_portfolio(db, obj_in=tx_in, portfolio_id=portfolio.id)
            holdings[ticker] = holdings.get(ticker, 0) + quantity
        else:  # is_sell
            # The validation logic to prevent selling more than is held exists in the
            # CRUD layer. We can simply attempt the transaction and let it fail if
            # holdings are insufficient.
            try:
                tx_in = schemas.TransactionCreate(
                    asset_id=asset_id,
                    transaction_type="SELL",
                    quantity=quantity,
                    price_per_unit=price,
                    transaction_date=tx_date.date(),
                )
                crud.transaction.create_with_portfolio(
                    db, obj_in=tx_in, portfolio_id=portfolio.id
                )
            except HTTPException:
                # This will likely fail if holdings are insufficient. We can just log it and move on.
                logger.info(f"Skipping SELL for {ticker} due to insufficient holdings.")

    db.commit() # Final commit for all created transactions
    logger.info(f"Successfully created {transactions_to_create} transactions for portfolio ID {portfolio.id}.")
    logger.info("--- Seeding complete ---")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_transactions(db)
    finally:
        db.close()