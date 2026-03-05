import sys
import os
import uuid
import time
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import event
from sqlalchemy.orm import Session

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app import models, schemas, crud
from app.db.session import SessionLocal

def count_queries(session):
    queries = []
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        queries.append(statement)

    event.listen(session.bind, "before_cursor_execute", before_cursor_execute)
    return queries

def setup_data(db: Session):
    # Create user
    user = models.User(
        email=f"test_{uuid.uuid4()}@example.com",
        hashed_password="hashed",
        is_active=True,
    )
    db.add(user)
    db.flush()

    # Create portfolio
    portfolio = models.Portfolio(name="Test Portfolio", user_id=user.id)
    db.add(portfolio)
    db.flush()

    # Create asset
    asset = models.Asset(
        ticker_symbol="TEST",
        name="Test Asset",
        asset_type="STOCK",
        currency="INR",
    )
    db.add(asset)
    db.flush()

    # Create another portfolio to host the "missing" BUY transactions
    portfolio2 = models.Portfolio(name="Other Portfolio", user_id=user.id)
    db.add(portfolio2)
    db.flush()

    num_sells = 50
    # Create BUY transactions in portfolio2 (so they won't be in portfolio1's get_multi_by_portfolio)
    buys = []
    for i in range(num_sells):
        buy = models.Transaction(
            user_id=user.id,
            portfolio_id=portfolio2.id,
            asset_id=asset.id,
            transaction_type="BUY",
            quantity=Decimal("10"),
            price_per_unit=Decimal("100"),
            transaction_date=datetime.now() - timedelta(days=20),
            fees=Decimal("0"),
        )
        db.add(buy)
        buys.append(buy)
    db.flush()

    # Create SELL transactions in portfolio
    sells = []
    for i in range(num_sells):
        sell = models.Transaction(
            user_id=user.id,
            portfolio_id=portfolio.id,
            asset_id=asset.id,
            transaction_type="SELL",
            quantity=Decimal("10"),
            price_per_unit=Decimal("110"),
            transaction_date=datetime.now() - timedelta(days=10),
            fees=Decimal("0"),
        )
        db.add(sell)
        sells.append(sell)
    db.flush()

    # Create links
    for i in range(num_sells):
        link = models.TransactionLink(
            sell_transaction_id=sells[i].id,
            buy_transaction_id=buys[i].id,
            quantity=Decimal("10"),
        )
        db.add(link)
    db.flush()
    db.commit()

    return portfolio.id

def run_benchmark():
    db = SessionLocal()
    try:
        portfolio_id = setup_data(db)

        # Clear cache or any pre-loaded objects if necessary
        db.expunge_all()

        queries = count_queries(db)

        print(f"Starting calculation for portfolio {portfolio_id}...")
        start_time = time.time()

        # We need to set up the environment for settings and other things if needed
        # But crud_holding might work with just db
        from app.crud.crud_holding import holding
        result = holding.get_portfolio_holdings_and_summary(db, portfolio_id=portfolio_id)

        end_time = time.time()

        print(f"Calculation took {end_time - start_time:.4f} seconds")
        print(f"Total queries: {len(queries)}")

        # Filter queries to see the N+1
        buy_tx_queries = [q for q in queries if 'FROM transactions' in q and 'WHERE transactions.id =' in q]
        print(f"Buy transaction lookup queries: {len(buy_tx_queries)}")

        # If N+1 is present, buy_tx_queries should be around num_sells (50)
        if len(buy_tx_queries) >= 50:
            print("N+1 Query detected!")
        else:
            print("N+1 Query NOT detected or not as expected.")

    finally:
        db.close()

if __name__ == "__main__":
    run_benchmark()
