import logging
import time
import uuid
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.cache.utils import cache_analytics_data
from app.models.user import User
from app.services.financial_data_service import financial_data_service

logger = logging.getLogger(__name__)


def _calculate_dashboard_summary(db: Session, *, user: User) -> Dict[str, Any]:
    """
    Calculates the dashboard summary metrics for a given user by aggregating
    summaries from all their portfolios.
    """
    start_time = time.time()
    from app import crud  # Local import to break circular dependency

    portfolios = crud.portfolio.get_multi_by_owner(db=db, user_id=user.id)
    if not portfolios:
        return {
            "total_value": Decimal("0.0"),
            "total_unrealized_pnl": Decimal("0.0"),
            "total_realized_pnl": Decimal("0.0"),
            "top_movers": [],
            "asset_allocation": [],
        }

    # Initialize aggregate values
    agg_total_value = Decimal("0.0")
    agg_total_unrealized_pnl = Decimal("0.0")
    agg_total_realized_pnl = Decimal("0.0")
    agg_holdings = []

    # Aggregate data from all portfolios
    for portfolio in portfolios:
        portfolio_data = crud.holding.get_portfolio_holdings_and_summary(
            db, portfolio_id=portfolio.id
        )
        summary = portfolio_data.summary

        agg_total_value += summary.total_value
        agg_total_unrealized_pnl += summary.total_unrealized_pnl
        agg_total_realized_pnl += summary.total_realized_pnl

        agg_holdings.extend(portfolio_data.holdings)

    # Calculate top movers from aggregated holdings
    top_movers = []
    for h in agg_holdings:
        # Only include assets with a non-zero day's P&L and a valid quantity
        if h.days_pnl is not None and h.days_pnl != 0 and h.quantity > 0:
            # This is already in INR after the holding.py fix
            daily_change_per_unit = h.days_pnl / h.quantity

            # The holding schema now contains the asset's currency.
            # We need to pass this to the frontend so it can display the correct
            # currency symbol for the `current_price`.
            asset_currency = "INR" # Default
            asset = crud.asset.get(db, id=h.asset_id)
            if asset:
                asset_currency = asset.currency

            top_movers.append(
                {
                    "ticker_symbol": h.ticker_symbol,
                    "currency": asset_currency,
                    "name": h.asset_name,
                    "current_price": h.current_price,
                    "daily_change": daily_change_per_unit,
                    "daily_change_percentage": h.days_pnl_percentage,
                }
            )
    top_movers.sort(key=lambda x: abs(x["daily_change_percentage"]), reverse=True)

    # Calculate asset allocation from aggregated holdings
    asset_allocation_map = defaultdict(Decimal)
    for h in agg_holdings:
        asset_allocation_map[h.ticker_symbol] += h.current_value

    formatted_allocation = [
        {"ticker": ticker, "value": value}
        for ticker, value in asset_allocation_map.items()
    ]

    end_time = time.time()
    logger.info(
        "Dashboard summary for user %s took %.4f seconds.",
        user.id,
        end_time - start_time,
    )
    return {
        "total_value": agg_total_value,
        "total_unrealized_pnl": agg_total_unrealized_pnl,
        "total_realized_pnl": agg_total_realized_pnl,
        "top_movers": top_movers[:5],
        "asset_allocation": formatted_allocation,
    }


def _get_portfolio_history(
    db: Session,
    *,
    user: User,
    range_str: str,
    portfolio_id: uuid.UUID | None = None,
) -> List[Dict[str, Any]]:
    """
    Calculates the portfolio's total value over a specified time range.

    Args:
        db: Database session
        user: The user whose portfolio history to calculate
        range_str: Time range ("7d", "30d", "1y", "all")
        portfolio_id: Optional. If provided, calculate history for only this
                      portfolio. If None, calculate for all user portfolios.
    """
    from sqlalchemy import func

    from app import crud, models  # Local import to break circular dependency
    from app.models.portfolio_snapshot import DailyPortfolioSnapshot

    end_date = date.today()
    if range_str == "7d":
        start_date = end_date - timedelta(days=7)
    elif range_str == "30d":
        start_date = end_date - timedelta(days=30)
    elif range_str == "1y":
        start_date = end_date - timedelta(days=365)
    else:  # "all"
        first_txn_query = db.query(crud.transaction.model).filter(
            crud.transaction.model.user_id == user.id
        )
        if portfolio_id:
            first_txn_query = first_txn_query.filter(
                crud.transaction.model.portfolio_id == portfolio_id
            )
        first_transaction = first_txn_query.order_by(
            crud.transaction.model.transaction_date.asc()
        ).first()
        start_date = (
            first_transaction.transaction_date.date() if first_transaction else end_date
        )

    # --- Pre-fetch Non-Market Assets for Historical Calculation ---
    from app.crud.crud_holding import (
        _calculate_fd_current_value,
        _calculate_rd_value_at_date,
    )
    from app.models.asset import Asset
    from app.models.fixed_deposit import FixedDeposit
    from app.models.recurring_deposit import RecurringDeposit

    fd_query = db.query(FixedDeposit)
    rd_query = db.query(RecurringDeposit)
    # Finding PPF assets to use with process_ppf_holding later if needed
    ppf_asset_query = db.query(Asset).filter(Asset.asset_type.in_(["PPF"]))

    if portfolio_id:
        fd_query = fd_query.filter(FixedDeposit.portfolio_id == portfolio_id)
        rd_query = rd_query.filter(RecurringDeposit.portfolio_id == portfolio_id)
        ppf_asset_query = ppf_asset_query.join(models.Transaction).filter(
            models.Transaction.portfolio_id == portfolio_id
        )
    else:
        # If 'all' portfolios, we still need to filter by user_id
        portfolios = (
            db.query(models.Portfolio)
            .filter(models.Portfolio.user_id == user.id)
            .all()
        )
        portfolio_ids = [p.id for p in portfolios]
        if portfolio_ids:
            fd_query = fd_query.filter(FixedDeposit.portfolio_id.in_(portfolio_ids))
            rd_query = rd_query.filter(RecurringDeposit.portfolio_id.in_(portfolio_ids))
            ppf_asset_query = ppf_asset_query.join(models.Transaction).filter(
                models.Transaction.user_id == user.id
            )

    all_fds = fd_query.all()
    all_rds = rd_query.all()
    ppf_assets = ppf_asset_query.distinct().all()

    # Pre-fetch PPF transactions if we have PPF assets
    ppf_transactions = []
    if ppf_assets:
        ppf_asset_ids = [a.id for a in ppf_assets]
        ppf_tx_query = db.query(models.Transaction).filter(
            models.Transaction.asset_id.in_(ppf_asset_ids),
            models.Transaction.transaction_date <= end_date
        )
        if portfolio_id:
            ppf_tx_query = ppf_tx_query.filter(
                models.Transaction.portfolio_id == portfolio_id
            )
        ppf_transactions = ppf_tx_query.all()

    # Fetch snapshots
    snapshot_query = db.query(
        DailyPortfolioSnapshot.snapshot_date,
        func.sum(DailyPortfolioSnapshot.total_value).label('total_value')
    ).join(models.Portfolio).filter(
        models.Portfolio.user_id == user.id,
        DailyPortfolioSnapshot.snapshot_date >= start_date,
        DailyPortfolioSnapshot.snapshot_date <= end_date
    )
    if portfolio_id:
        snapshot_query = snapshot_query.filter(models.Portfolio.id == portfolio_id)

    snapshot_query = snapshot_query.group_by(DailyPortfolioSnapshot.snapshot_date)

    snapshot_data = {row.snapshot_date: row.total_value for row in snapshot_query.all()}


    # Build asset query with optional portfolio filter
    asset_query = (
        db.query(crud.asset.model)
        .join(crud.transaction.model)
        .filter(crud.transaction.model.user_id == user.id)
    )
    if portfolio_id:
        asset_query = asset_query.filter(
            crud.transaction.model.portfolio_id == portfolio_id
        )
    all_user_assets = asset_query.distinct().all()

    if not all_user_assets:
        return []

    # Filter for assets that are likely to have market data from yfinance/amfi
    supported_types = [
        "STOCK", "ETF", "MUTUAL_FUND", "MUTUAL FUND", "BOND",
    ]
    market_traded_assets = [
        asset for asset in all_user_assets
        if str(asset.asset_type).upper().replace("_", " ") in supported_types
    ]

    asset_map = {a.ticker_symbol: a for a in market_traded_assets}

    asset_details_list = [
        {
            "ticker_symbol": asset.ticker_symbol,
            "exchange": asset.exchange,
            "asset_type": asset.asset_type,
        }
        for asset in market_traded_assets
    ]

    historical_prices = financial_data_service.get_historical_prices(
        assets=asset_details_list, start_date=start_date, end_date=end_date
    )

    # --- FX Rate Handling ---
    foreign_currencies = {
        asset.currency for asset in market_traded_assets
        if asset.currency and asset.currency.upper() != "INR"
    }

    fx_rates_history = {}
    if foreign_currencies:
        logger.debug(f"Fetching FX history for currencies: {foreign_currencies}")
        fx_tickers_list = [
            {"ticker_symbol": f"{curr}INR=X", "exchange": None}
            for curr in foreign_currencies
        ]
        fx_rates_history = financial_data_service.get_historical_prices(
            assets=fx_tickers_list, start_date=start_date, end_date=end_date
        )

    # Build transactions query with optional portfolio filter
    txn_query = db.query(crud.transaction.model).filter(
        crud.transaction.model.user_id == user.id,
        crud.transaction.model.transaction_date <= end_date,
    )
    if portfolio_id:
        txn_query = txn_query.filter(
            crud.transaction.model.portfolio_id == portfolio_id
        )
    transactions = txn_query.order_by(
        crud.transaction.model.transaction_date.asc()
    ).all()

    history_points = []
    current_day = start_date
    transaction_idx = 0
    daily_holdings = defaultdict(Decimal)
    last_known_prices = {}
    last_known_fx_rates = {}

    # Calculate initial holdings up to the start_date
    initial_transactions = [
        t for t in transactions if t.transaction_date.date() < start_date
    ]
    for t in initial_transactions:
        ticker = t.asset.ticker_symbol
        if (
            t.transaction_type.lower() == "buy"
            or t.transaction_type == "RSU_VEST"
            or t.transaction_type == "ESPP_PURCHASE"
        ):
            daily_holdings[ticker] += t.quantity
        elif t.transaction_type.lower() == "sell":
            daily_holdings[ticker] -= t.quantity

    # Pre-fill last known prices for the day before the window starts
    day_before_start = start_date - timedelta(days=1)

    # 1. Pre-fill Asset Prices
    for ticker in daily_holdings:
        if ticker in historical_prices:
            # Find the most recent price on or before the day before the window
            relevant_dates = [
                d for d in historical_prices[ticker] if d <= day_before_start
            ]
            if relevant_dates:
                last_known_prices[ticker] = historical_prices[ticker][
                    max(relevant_dates)
                ]

    # 2. Pre-fill FX Rates
    for curr in foreign_currencies:
        fx_ticker = f"{curr}INR=X"
        if fx_ticker in fx_rates_history:
            relevant_dates = [
                d for d in fx_rates_history[fx_ticker] if d <= day_before_start
            ]
            if relevant_dates:
                last_known_fx_rates[fx_ticker] = fx_rates_history[fx_ticker][
                    max(relevant_dates)
                ]

    transaction_idx = len(initial_transactions)

    while current_day <= end_date:
        while (
            transaction_idx < len(transactions)
            and transactions[transaction_idx].transaction_date.date() == current_day
        ):
            t = transactions[transaction_idx]
            ticker = t.asset.ticker_symbol
            if (
                t.transaction_type.lower() == "buy"
                or t.transaction_type == "RSU_VEST"
                or t.transaction_type == "ESPP_PURCHASE"
            ):
                daily_holdings[ticker] += t.quantity
            elif t.transaction_type.lower() == "sell":
                daily_holdings[ticker] -= t.quantity
            transaction_idx += 1

        # Update FX rates for today if available
        for curr in foreign_currencies:
            fx_ticker = f"{curr}INR=X"
            if (
                fx_ticker in fx_rates_history
                and current_day in fx_rates_history[fx_ticker]
            ):
                last_known_fx_rates[fx_ticker] = fx_rates_history[fx_ticker][
                    current_day
                ]

        # Ignore snapshots for today, as the market may still be open.
        # Live calculation preferred.
        if current_day in snapshot_data and current_day != end_date:
            day_total_value = snapshot_data[current_day]
            # Update last_known_prices for potential future days without snapshots
            for ticker, quantity in daily_holdings.items():
                if quantity > 0:
                    hist_prices = historical_prices.get(ticker)
                    if hist_prices and current_day in hist_prices:
                        last_known_prices[ticker] = hist_prices[current_day]
        else:
            day_total_value = Decimal("0.0")

            # For the current day (end_date), we want absolute precision including
            # all fixed-income assets (FDs, PPF, Bonds) which aren't in
            # historical_prices.
            # We fetch the live holdings summary to get the exact true current value.
            if current_day == end_date:
                try:
                    portfolio_data = crud.holding.get_portfolio_holdings_and_summary(
                        db, portfolio_id=portfolio_id
                    ) if portfolio_id else None

                    if portfolio_data:
                        day_total_value = portfolio_data.summary.total_value
                    else:
                        # If calculating for 'all' portfolios, we have to sum them up
                        portfolios = crud.portfolio.get_multi_by_owner(
                            db=db, user_id=user.id
                        )
                        for p in portfolios:
                            p_data = crud.holding.get_portfolio_holdings_and_summary(
                                db, portfolio_id=p.id
                            )
                            day_total_value += p_data.summary.total_value
                except Exception as e:
                    logger.error(f"Error calculating live holdings for today: {e}")
                    # Fallback to the manual sum below if the live summary fails
                    pass

            # If it's not the end_date, OR if the live calculation failed/returned 0,
            # calculate historical value using the manual ticker * price loop
            # + Fixed Income math.
            if day_total_value == Decimal("0.0"):
                # 1. Market-Traded Assets
                for ticker, quantity in daily_holdings.items():
                    if quantity > 0:
                        hist_prices = historical_prices.get(ticker)
                        if hist_prices and current_day in hist_prices:
                            last_known_prices[ticker] = hist_prices[current_day]

                        if ticker in last_known_prices:
                            price = last_known_prices[ticker]

                            # Convert to INR if foreign asset
                            asset = asset_map.get(ticker)
                            if (
                                asset
                                and asset.currency
                                and asset.currency.upper() != "INR"
                            ):
                                fx_ticker = f"{asset.currency}INR=X"
                                fx_rate = last_known_fx_rates.get(fx_ticker, Decimal(1))
                                price = price * fx_rate

                            day_total_value += quantity * price

                # 2. Fixed Deposits (Simulated for this historical day)
                for fd in all_fds:
                    # Ignore if the FD hasn't started yet on this historical date
                    if fd.start_date > current_day:
                        continue

                    # If matured before this historical date, value is fixed at maturity
                    calc_date = (
                        current_day
                        if current_day <= fd.maturity_date
                        else fd.maturity_date
                    )

                    fd_val = _calculate_fd_current_value(
                        fd.principal_amount,
                        fd.interest_rate,
                        fd.start_date,
                        calc_date,
                        fd.compounding_frequency,
                        fd.interest_payout,
                    )

                    # If it's a payout FD, it stays at principal. We don't add paid
                    # interest to portfolio value unless it was reinvested (which would
                    # be separate transactions).
                    # If it matured and paid out, it theoretically "leaves" the
                    # portfolio unless we track cash.
                    # Since we don't track cash yet, we zero out matured payout FDs
                    # and matured Cumulative FDs to match how we handle sold stocks.
                    if current_day > fd.maturity_date:
                        # Matured. Ensure we only add it if it's considered "active"
                        # or we decide to keep matured investments as permanent
                        # fixtures (which is unrealistic).
                        # Let's align with get_portfolio_holdings_and_summary: matured
                        # FDs are returned, but their maturity value is just the
                        # principal (for payout) or maturity_value (for cumulative).
                        day_total_value += fd_val
                    else:
                        day_total_value += fd_val

                # 3. Recurring Deposits (Simulated for this historical day)
                from dateutil.relativedelta import relativedelta
                for rd in all_rds:
                    if rd.start_date > current_day:
                        continue

                    rd_maturity_date = rd.start_date + relativedelta(
                        months=rd.tenure_months
                    )
                    calc_date = (
                        current_day
                        if current_day <= rd_maturity_date
                        else rd_maturity_date
                    )

                    rd_val = _calculate_rd_value_at_date(
                        rd.monthly_installment,
                        rd.interest_rate,
                        rd.start_date,
                        rd.tenure_months,
                        calc_date,
                    )

                    # If simulating a date during the RD, we ensure we only count
                    # the installments paid up to that date.
                    # _calculate_rd_value_at_date inherently handles this correctly
                    # using `calculation_date`.
                    # However, if it hasn't matured yet, we also must ensure
                    # total_invested logic acts dynamically.
                    installments_to_date = 0
                    temp_date = rd.start_date
                    while (
                        temp_date <= current_day
                        and installments_to_date < rd.tenure_months
                    ):
                        installments_to_date += 1
                        temp_date += relativedelta(months=1)

                    if installments_to_date > 0:
                        day_total_value += rd_val

                # 4. PPF (Simulated for this historical day)
                from app.crud.crud_ppf import process_ppf_holding
                if ppf_assets:
                    # Filter PPF transactions up to the current historical day
                    day_ppf_txns = [
                        tx for tx in ppf_transactions
                        if tx.transaction_date.date() <= current_day
                    ]

                    for asset in ppf_assets:
                        asset_txns = [
                            tx for tx in day_ppf_txns if tx.asset_id == asset.id
                        ]
                        if not asset_txns:
                            continue

                        # process_ppf_holding requires a calculation date for interest
                        try:
                            ppf_holding = process_ppf_holding(
                                db=db,
                                ppf_asset=asset,
                                portfolio_id=portfolio_id,
                                calculation_date=current_day,
                                simulate_only=True,
                            )
                            day_total_value += ppf_holding.current_value
                        except Exception as e:
                            logger.error(
                                f"Error calculating historical PPF for "
                                f"{current_day}: {e}"
                            )

        history_points.append({"date": current_day, "value": day_total_value})
        current_day += timedelta(days=1)

    return history_points


class CRUDDashboard:
    @cache_analytics_data(prefix="analytics:dashboard_summary", arg_names=["user_id"])
    def get_summary(self, db: Session, *, user_id: uuid.UUID) -> Dict[str, Any]:
        user = db.get(User, user_id)
        if not user:
            # This case should ideally not be hit if called from a valid session
            return {}
        return _calculate_dashboard_summary(db=db, user=user)

    @cache_analytics_data(
        prefix="analytics:dashboard_history", arg_names=["user", "range_str"]
    )
    def get_history(
        self, db: Session, *, user: User, range_str: str
    ) -> List[Dict[str, Any]]:
        return _get_portfolio_history(db=db, user=user, range_str=range_str)

    def get_allocation(
        self, db: Session, *, user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        # Note: This will not be cached independently. It will be fast if get_summary
        # has been called recently, as the underlying calculation will be cached.
        summary_data = self.get_summary(db=db, user_id=user_id)
        return summary_data.get("asset_allocation", [])


dashboard = CRUDDashboard()
