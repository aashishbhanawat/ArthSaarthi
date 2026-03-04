import os
import sys
import time
import uuid
from decimal import Decimal
from datetime import date, timedelta

# Add backend to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base_class import Base
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.asset import Asset
from app.models.transaction import Transaction
from app.models.transaction_link import TransactionLink
from app.models.recurring_deposit import RecurringDeposit
from app.models.fixed_deposit import FixedDeposit
from app.models.portfolio_snapshot import DailyPortfolioSnapshot
from app.schemas.enums import TransactionType
from sqlalchemy import event

# Set a dummy SECRET_KEY for config
os.environ["SECRET_KEY"] = "dummy"

# Create in-memory SQLite database
engine = create_engine("sqlite:///:memory:", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import all models to ensure they are registered with Base
from app import models
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Tracking query count
query_count = 0

@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    global query_count
    query_count += 1

def setup_data(num_portfolios=10, txs_per_portfolio=5):
    # Create user
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="dummy",
        is_active=True,
    )
    db.add(user)
    db.commit()

    # Create common assets
    assets = []
    for i in range(5):
        asset = Asset(
            id=uuid.uuid4(),
            name=f"Asset {i}",
            asset_type="STOCK",
            ticker_symbol=f"TICK{i}",
            currency="INR"
        )
        assets.append(asset)
        db.add(asset)
    db.commit()

    # Create portfolios and transactions
    for i in range(num_portfolios):
        portfolio = Portfolio(
            id=uuid.uuid4(),
            user_id=user.id,
            name=f"Portfolio {i}"
        )
        db.add(portfolio)
        db.commit()

        for j in range(txs_per_portfolio):
            tx = Transaction(
                id=uuid.uuid4(),
                user_id=user.id,
                portfolio_id=portfolio.id,
                asset_id=assets[j % len(assets)].id,
                transaction_type=TransactionType.BUY,
                quantity=Decimal("10"),
                price_per_unit=Decimal("100"),
                transaction_date=date.today() - timedelta(days=j),
                details={}
            )
            db.add(tx)
        db.commit()

    return user

def run_benchmark():
    from app.crud.crud_dashboard import dashboard

    user = setup_data(num_portfolios=20, txs_per_portfolio=10)

    global query_count

    # 1. Benchmark dashboard summary
    query_count = 0
    start = time.time()
    # Mocking out the external API calls since this is just a DB benchmark
    # The external calls in _process_market_traded_assets might fail without mocking,
    # but we will patch them for the test

    from unittest.mock import patch
    with patch('app.services.financial_data_service.financial_data_service.get_current_prices', return_value={}):
        dashboard.get_summary(db=db, user_id=user.id)

    end = time.time()
    print(f"--- Dashboard Summary ---")
    print(f"Time: {end - start:.4f} seconds")
    print(f"Queries: {query_count}")

    # 2. Benchmark dashboard history
    query_count = 0
    start = time.time()

    with patch('app.services.financial_data_service.financial_data_service.get_historical_prices', return_value={}), \
         patch('app.services.financial_data_service.financial_data_service.get_current_prices', return_value={}):
        # "all" range will trigger the `if current_day == end_date:` block
        dashboard.get_history(db=db, user=user, range_str="all")

    end = time.time()
    print(f"\n--- Dashboard History ('all') ---")
    print(f"Time: {end - start:.4f} seconds")
    print(f"Queries: {query_count}")

if __name__ == "__main__":
    run_benchmark()
