import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app import crud
from app.models.portfolio import Portfolio
from app.models.portfolio_snapshot import DailyPortfolioSnapshot
from app.schemas.holding import PortfolioHoldingsAndSummary

logger = logging.getLogger(__name__)


def take_snapshot_for_portfolio(
    db: Session, portfolio_id: str, target_date: Optional[date] = None
) -> DailyPortfolioSnapshot:
    """
    Calculates the current value and holdings of a portfolio and saves it
    as a snapshot for the given date (defaults to today).
    Note: Since this relies on live market prices, it should be called on the
    actual date we want to snapshot.
    """
    if target_date is None:
        target_date = date.today()

    logger.info(f"Taking snapshot for portfolio {portfolio_id} on {target_date}")

    # Calculate current state
    portfolio_data: PortfolioHoldingsAndSummary = (
        crud.holding.get_portfolio_holdings_and_summary(db, portfolio_id=portfolio_id)
    )

    summary = portfolio_data.summary
    holdings = portfolio_data.holdings

    equity_val = Decimal("0.0")
    mf_val = Decimal("0.0")
    bond_val = Decimal("0.0")
    fd_val = Decimal("0.0")

    holdings_json = []

    for h in holdings:
        val = h.current_value
        asset_type = str(h.asset_type).upper().replace("_", " ")

        if asset_type in ["STOCK", "ETF"]:
            equity_val += val
        elif asset_type in ["MUTUAL FUND", "MUTUAL_FUND"]:
            mf_val += val
        elif asset_type == "BOND":
            bond_val += val
        elif asset_type in [
            "FIXED DEPOSIT",
            "RECURRING DEPOSIT",
            "PPF",
            "FIXED_DEPOSIT",
            "RECURRING_DEPOSIT",
        ]:
            fd_val += val

        # Serialize holding for JSON snapshot
        holdings_json.append({
            "ticker_symbol": h.ticker_symbol,
            "asset_name": h.asset_name,
            "asset_type": h.asset_type,
            "quantity": float(h.quantity),
            "current_price": float(h.current_price) if h.current_price else None,
            "current_value": float(h.current_value) if h.current_value else None,
            "currency": h.currency,
        })

    # Upsert the snapshot based on active database dialect
    values = dict(
        portfolio_id=portfolio_id,
        snapshot_date=target_date,
        total_value=summary.total_value,
        equity_value=equity_val,
        mf_value=mf_val,
        bond_value=bond_val,
        fd_value=fd_val,
        holdings_snapshot=holdings_json,
    )

    dialect_name = db.bind.dialect.name if db.bind else "postgresql"
    insert_fn = sqlite_insert if dialect_name == "sqlite" else pg_insert

    stmt = insert_fn(DailyPortfolioSnapshot).values(**values)

    # If a snapshot for this date already exists, update it with fresh values
    stmt = stmt.on_conflict_do_update(
        index_elements=['portfolio_id', 'snapshot_date'],
        set_={
            'total_value': stmt.excluded.total_value,
            'equity_value': stmt.excluded.equity_value,
            'mf_value': stmt.excluded.mf_value,
            'bond_value': stmt.excluded.bond_value,
            'fd_value': stmt.excluded.fd_value,
            'holdings_snapshot': stmt.excluded.holdings_snapshot,
            'updated_at': stmt.excluded.updated_at,
        }
    ).returning(DailyPortfolioSnapshot)

    result = db.execute(stmt)
    snapshot = result.scalar_one()
    db.commit()

    return snapshot


def take_daily_snapshots_for_all(db: Session) -> int:
    """
    Iterates through all portfolios in the system and takes a snapshot for today.
    Returns the number of snapshots created/updated.
    """
    portfolios = db.query(Portfolio).all()
    count = 0
    today = date.today()

    for portfolio in portfolios:
        try:
            take_snapshot_for_portfolio(db, portfolio.id, target_date=today)
            count += 1
        except Exception as e:
            logger.error(f"Failed to take snapshot for portfolio {portfolio.id}: {e}")
            db.rollback()

    return count
