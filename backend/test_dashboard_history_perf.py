import sys
import os
import uuid
import time
from decimal import Decimal
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set up path to import app modules
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.db.base import Base
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.asset import Asset
from app.models.transaction import Transaction
from app.models.portfolio_snapshot import DailyPortfolioSnapshot
from app.crud.crud_dashboard import _get_portfolio_history

# Setup in-memory SQLite DB
engine = create_engine("sqlite:///:memory:", echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Seed data
user = User(id=uuid.uuid4(), email="test@test.com", hashed_password="hashed_password", is_active=True)
db.add(user)
portfolio = Portfolio(id=uuid.uuid4(), name="Test Portfolio", user_id=user.id)
db.add(portfolio)

# Create 50 assets
assets = []
for i in range(50):
    asset = Asset(
        id=uuid.uuid4(),
        ticker_symbol=f"STOCK{i}",
        name=f"Stock {i}",
        asset_type="STOCK",
        currency="INR"
    )
    db.add(asset)
    assets.append(asset)

db.commit()

# Create 1000 transactions over the last 1 year
end_date = date.today()
start_date = end_date - timedelta(days=365)

import random

for i in range(1000):
    # Random date within the last year
    days_ago = random.randint(0, 365)
    tx_date = end_date - timedelta(days=days_ago)

    asset = random.choice(assets)

    tx = Transaction(
        id=uuid.uuid4(),
        user_id=user.id,
        portfolio_id=portfolio.id,
        asset_id=asset.id,
        transaction_type="BUY" if random.random() > 0.3 else "SELL",
        quantity=Decimal("10.0"),
        price_per_unit=Decimal("100.0"),
        transaction_date=tx_date,
    )
    db.add(tx)

db.commit()

# Enable query logging to count queries
import sqlalchemy
query_count = 0
@sqlalchemy.event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    global query_count
    query_count += 1

print("Starting _get_portfolio_history calculation...")
start_time = time.time()
_get_portfolio_history(db=db, user=user, range_str="1y", portfolio_id=portfolio.id)
end_time = time.time()

print(f"Execution time: {end_time - start_time:.4f} seconds")
print(f"Total queries executed: {query_count}")
