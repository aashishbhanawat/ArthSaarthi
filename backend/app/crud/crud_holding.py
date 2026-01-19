import logging
import math
import time
import uuid
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import List

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.cache.utils import cache_analytics_data
from app.core.config import settings
from app.crud.crud_ppf import process_ppf_holding
from app.models.recurring_deposit import RecurringDeposit
from app.models.transaction_link import TransactionLink
from app.schemas.enums import BondType, TransactionType
from app.services.financial_data_service import financial_data_service

logger = logging.getLogger(__name__)


def _calculate_fd_current_value(
    principal: Decimal,
    interest_rate: Decimal,
    start_date: date,
    end_date: date,
    compounding_frequency: str,
    interest_payout: str,
) -> Decimal:
    """
    Calculates the current value of an FD.
    For cumulative FDs, it uses compound interest.
    For payout FDs, it returns the principal.
    """
    # Payout FDs always return principal (interest is paid separately)
    if (interest_payout or "").upper() != "CUMULATIVE":
        return principal

    if end_date < start_date:
        return principal

    # Normalize compounding frequency
    compounding_frequency_map = {
        "ANNUALLY": 1,
        "SEMI-ANNUALLY": 2,
        "QUARTERLY": 4,
        "MONTHLY": 12,
    }
    n = Decimal(compounding_frequency_map.get(
        (compounding_frequency or "").upper(), 4
    ))  # Default to quarterly

    t = Decimal((end_date - start_date).days / 365.25)
    r = Decimal(interest_rate / 100)
    current_value = principal * ((1 + r / n) ** (n * t))
    return current_value


def _calculate_total_interest_paid(fd: models.FixedDeposit, end_date: date) -> Decimal:
    """Calculates the total interest paid for a payout FD up to a given end date."""
    # Cumulative FDs don't pay interest until maturity
    if (fd.interest_payout or "").upper() == "CUMULATIVE":
        return Decimal(0)

    payout_frequency_map = {
        "MONTHLY": 1,
        "QUARTERLY": 3,
        "HALF_YEARLY": 6,
        "SEMI-ANNUALLY": 6,  # Alias for compatibility
        "ANNUALLY": 12,
    }
    months_interval = payout_frequency_map.get(fd.compounding_frequency.upper())

    if not months_interval:
        return Decimal(0)

    payouts_per_year = Decimal("12.0") / Decimal(str(months_interval))
    payout_rate = fd.interest_rate / Decimal("100.0") / payouts_per_year
    interest_per_payout = fd.principal_amount * payout_rate

    total_interest = Decimal(0)
    payout_date = fd.start_date + relativedelta(months=months_interval)
    while payout_date <= end_date:
        total_interest += interest_per_payout
        payout_date += relativedelta(months=months_interval)
    return total_interest


def _calculate_rd_value_at_date(
    monthly_installment: Decimal,
    interest_rate: Decimal,
    start_date: date,
    tenure_months: int,
    calculation_date: date,
) -> Decimal:
    """
    Calculates the value of a recurring deposit at a specific date by calculating
    the future value of each installment.
    """
    # Standard formula for RD maturity value with quarterly compounding.
    # M = P * [((1 + r/n)^(n*t) - 1) / (1 - (1+r/n)^(-1/3))]
    # where n=4 for quarterly. This iterative approach is equivalent and clearer.
    total_value = Decimal("0.0")
    quarterly_rate = interest_rate / Decimal("400.0")  # r/n where n=4, and r is in %

    num_installments = min(
        tenure_months,
        (calculation_date.year - start_date.year) * 12
        + (calculation_date.month - start_date.month)
        + 1,
    )

    for i in range(num_installments):
        _ = start_date + relativedelta(months=i)
        num_quarters = Decimal(num_installments - i) / 3
        total_value += monthly_installment * (1 + quarterly_rate) ** num_quarters

    return total_value.quantize(Decimal("0.01"))


def _process_fixed_deposits(
    all_fixed_deposits: List[models.FixedDeposit],
) -> tuple[list[schemas.Holding], Decimal]:
    """Processes all fixed deposits, separating active and matured ones."""
    holdings_list = []
    total_realized_pnl = Decimal("0.0")
    today = date.today()

    active_fds = [fd for fd in all_fixed_deposits if fd.maturity_date >= today]
    matured_fds = [fd for fd in all_fixed_deposits if fd.maturity_date < today]

    for fd in matured_fds:
        if fd.interest_payout != "Cumulative":
            total_realized_pnl += _calculate_total_interest_paid(fd, fd.maturity_date)
        else:
            maturity_value = _calculate_fd_current_value(
                fd.principal_amount,
                fd.interest_rate,
                fd.start_date,
                fd.maturity_date,
                fd.compounding_frequency,
                fd.interest_payout,
            )
            total_realized_pnl += maturity_value - fd.principal_amount

    for fd in active_fds:
        interest_paid_to_date = _calculate_total_interest_paid(fd, today)

        current_value = _calculate_fd_current_value(
            fd.principal_amount,
            fd.interest_rate,
            fd.start_date,
            today,
            fd.compounding_frequency,
            fd.interest_payout,
        )
        unrealized_pnl = current_value - fd.principal_amount
        unrealized_pnl_percentage = (
            float(unrealized_pnl / fd.principal_amount)
            if fd.principal_amount > 0
            else 0.0
        )
        holdings_list.append(
            schemas.Holding(
                asset_id=fd.id,
                ticker_symbol=fd.account_number,
                asset_name=fd.name,
                asset_type="FIXED_DEPOSIT",
                currency="INR",
                group="DEPOSITS",
                quantity=Decimal(1),
                average_buy_price=fd.principal_amount,
                total_invested_amount=fd.principal_amount,
                current_price=current_value,
                current_value=current_value,
                days_pnl=Decimal(0),
                days_pnl_percentage=0.0,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_percentage=unrealized_pnl_percentage,
                realized_pnl=interest_paid_to_date,
                interest_rate=fd.interest_rate,
                maturity_date=fd.maturity_date,
                account_number=fd.account_number,
            )
        )
    return holdings_list, total_realized_pnl


def _process_recurring_deposits(
    all_recurring_deposits: List[RecurringDeposit],
) -> tuple[list[schemas.Holding], Decimal]:
    """Processes all recurring deposits, separating active and matured ones."""
    holdings_list = []
    total_realized_pnl = Decimal("0.0")
    today = date.today()

    active_rds = [
        rd
        for rd in all_recurring_deposits
        if (rd.start_date + relativedelta(months=rd.tenure_months)) >= today
    ]
    matured_rds = [
        rd
        for rd in all_recurring_deposits
        if (rd.start_date + relativedelta(months=rd.tenure_months)) < today
    ]

    for rd in matured_rds:
        maturity_date = rd.start_date + relativedelta(months=rd.tenure_months)
        maturity_value = _calculate_rd_value_at_date(
            rd.monthly_installment,
            rd.interest_rate,
            rd.start_date,
            rd.tenure_months,
            maturity_date,
        )
        total_invested = rd.monthly_installment * rd.tenure_months
        total_realized_pnl += maturity_value - total_invested

    for rd in active_rds:
        current_value = _calculate_rd_value_at_date(
            rd.monthly_installment,
            rd.interest_rate,
            rd.start_date,
            rd.tenure_months,
            today,
        )

        installments_paid = 0
        temp_date = rd.start_date
        while temp_date <= today and installments_paid < rd.tenure_months:
            installments_paid += 1
            temp_date += relativedelta(months=1)

        total_invested = rd.monthly_installment * installments_paid
        if total_invested <= 0:
            continue

        unrealized_pnl = current_value - total_invested
        unrealized_pnl_percentage = (
            float(unrealized_pnl / total_invested) if total_invested > 0 else 0.0
        )

        holdings_list.append(
            schemas.Holding(
                asset_id=rd.id,
                asset_name=rd.name,
                currency="INR",
                asset_type="RECURRING_DEPOSIT",
                group="DEPOSITS",
                quantity=Decimal(1),
                average_buy_price=total_invested,
                total_invested_amount=total_invested,
                current_price=current_value,
                current_value=current_value,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_percentage=unrealized_pnl_percentage,
                interest_rate=rd.interest_rate,
                maturity_date=rd.start_date + relativedelta(months=rd.tenure_months),
                ticker_symbol=rd.account_number or rd.name,
                account_number=rd.account_number,
                days_pnl=Decimal(0),
                days_pnl_percentage=0.0,
            )
        )
    return holdings_list, total_realized_pnl


def _calculate_summary(
    holdings_list: List[schemas.Holding],
    realized_pnl_from_other_sources: Decimal,
    transactions: List[models.Transaction],
) -> schemas.PortfolioSummary:
    """Calculates the final portfolio summary from a list of holdings."""
    summary_total_value = Decimal("0.0")
    summary_total_invested = Decimal("0.0")
    summary_days_pnl = Decimal("0.0")
    summary_total_unrealized_pnl = Decimal("0.0")
    logger.debug(
        "[_calculate_summary] Initializing summary calculation. "
        "Realized PNL from other sources: %s", realized_pnl_from_other_sources
    )
    summary_total_realized_pnl = realized_pnl_from_other_sources
    logger.debug(
        "[_calculate_summary] Initial realized PNL from sources: %s",
        summary_total_realized_pnl,
    )
    for holding_item in holdings_list:
        summary_total_value += holding_item.current_value
        summary_total_invested += holding_item.total_invested_amount
        summary_total_unrealized_pnl += holding_item.unrealized_pnl or 0
        # Realized PNL from active holdings (e.g., Payout FDs) is added here.
        # PNL from sold/income events on market-traded assets is already in
        # realized_pnl_from_other_sources. We only add PNL from non-market assets here.
        asset_type_upper = str(holding_item.asset_type).upper()
        if asset_type_upper in ["FIXED_DEPOSIT", "RECURRING_DEPOSIT"]:
            summary_total_realized_pnl += holding_item.realized_pnl or 0
        summary_days_pnl += holding_item.days_pnl
    logger.debug(
        "[_calculate_summary] Final calculated total realized PNL: %s",
        summary_total_realized_pnl,
    )

    return schemas.PortfolioSummary(
        total_value=summary_total_value,
        total_invested_amount=summary_total_invested,
        days_pnl=summary_days_pnl,
        total_unrealized_pnl=summary_total_unrealized_pnl,
        total_realized_pnl=summary_total_realized_pnl,
    )


def _process_market_traded_assets(
    db: Session,
    portfolio_id: uuid.UUID,
    transactions: List[models.Transaction],
    initial_realized_pnl: Decimal,
) -> tuple[List[schemas.Holding], Decimal]:
    """Processes all market-traded assets like Stocks, MFs, ETFs, and Bonds."""
    holdings_list = []
    total_realized_pnl = initial_realized_pnl

    # This query is the key fix. It was missing. We need to find all unique
    # assets that have had any kind of transaction to be considered for holdings.
    unique_asset_ids_query = (
        db.query(models.Transaction.asset_id)
        .filter(models.Transaction.portfolio_id == portfolio_id)
        .filter(models.Transaction.transaction_type.in_([
            "BUY", "SELL", "RSU_VEST", "ESPP_PURCHASE", "SPLIT",
            "BONUS", "MERGER", "RENAME", "DEMERGER"
        ]))
        .distinct()
    )
    unique_asset_ids = [row[0] for row in unique_asset_ids_query.all()]

    holdings_state = defaultdict(
        lambda: {
            "quantity": Decimal("0.0"),
            "total_invested": Decimal("0.0"),
            "realized_pnl": Decimal("0.0"),
        }
    )

    portfolio_assets = (
        db.query(models.Asset).filter(models.Asset.id.in_(unique_asset_ids)).all()
    )
    asset_map = {asset.id: asset for asset in portfolio_assets}

    # Sort transactions by date to ensure chronological processing
    transactions.sort(key=lambda tx: tx.transaction_date)

    # --- Pre-fetch Transaction Links ---
    transaction_ids = [tx.id for tx in transactions]
    links = db.query(TransactionLink).filter(
        TransactionLink.sell_transaction_id.in_(transaction_ids)
    ).all()

    sell_links_map = defaultdict(list)
    for link in links:
        sell_links_map[link.sell_transaction_id].append(link)

    # Map transaction ID to object for quick lookup of Buy price
    tx_map = {tx.id: tx for tx in transactions}

    for tx in transactions:
        asset = asset_map.get(tx.asset_id)
        ticker = asset.ticker_symbol if asset else None
        if not ticker:
            continue # Should not happen if data is consistent

        acquisition_types = ["BUY", "ESPP_PURCHASE", "RSU_VEST"]
        if tx.transaction_type in acquisition_types:
            fx_rate = (
                Decimal(str(tx.details.get("fx_rate", 1))) if tx.details else Decimal(1)
            )
            holdings_state[ticker]["quantity"] += tx.quantity

            if tx.transaction_type == "RSU_VEST" and tx.details:
                cost_basis_price = Decimal(str(tx.details.get("fmv", 0)))
            else: # For BUY and ESPP, cost basis is the actual price paid.
                cost_basis_price = tx.price_per_unit
            cost_in_inr = tx.quantity * cost_basis_price * fx_rate
            holdings_state[ticker]["total_invested"] += cost_in_inr
        elif tx.transaction_type == "DIVIDEND":
            fx_rate = (
                Decimal(str(tx.details.get("fx_rate", 1))) if tx.details else Decimal(1)
            )
            dividend_amount = tx.quantity * tx.price_per_unit * fx_rate
            total_realized_pnl += dividend_amount
            holdings_state[ticker]["realized_pnl"] += dividend_amount
        elif tx.transaction_type == "COUPON":
            fx_rate = (
                Decimal(str(tx.details.get("fx_rate", 1))) if tx.details else Decimal(1)
            )
            # Coupons are usually cash amounts, but quantity * price fits the model if
            # quantity is the amount
            coupon_amount = tx.quantity * tx.price_per_unit * fx_rate
            total_realized_pnl += coupon_amount
            holdings_state[ticker]["realized_pnl"] += coupon_amount
        elif tx.transaction_type == TransactionType.SPLIT:
            if holdings_state[ticker]["quantity"] > 0 and tx.price_per_unit > 0:
                ratio = tx.quantity / tx.price_per_unit
                holdings_state[ticker]["quantity"] *= ratio
                if asset and asset.currency == "INR":
                    holdings_state[ticker]["quantity"] = Decimal(
                        math.floor(holdings_state[ticker]["quantity"])
                    )

        elif tx.transaction_type == TransactionType.MERGER:
            # MERGER: Zero out old holdings - shares have been converted to new asset
            # The BUY transaction for new shares was created by the merger handler
            logger.debug(
                f"Processing MERGER for {ticker}. Zeroing out old holdings."
            )
            holdings_state[ticker]["quantity"] = Decimal("0.0")
            holdings_state[ticker]["total_invested"] = Decimal("0.0")

        elif tx.transaction_type == TransactionType.RENAME:
            # RENAME: Zero out old holdings - shares transferred to new ticker
            # The BUY transaction for new ticker was created by the rename handler
            logger.debug(
                f"Processing RENAME for {ticker}. Zeroing out old holdings."
            )
            holdings_state[ticker]["quantity"] = Decimal("0.0")
            holdings_state[ticker]["total_invested"] = Decimal("0.0")

        elif tx.transaction_type == TransactionType.DEMERGER:
            # DEMERGER: Reduce parent's cost basis by absolute amount allocated
            # Use total_cost_allocated for absolute subtraction (multi-demerger safe)
            if tx.details and "total_cost_allocated" in tx.details:
                cost_to_subtract = Decimal(str(tx.details["total_cost_allocated"]))
                old_cost = holdings_state[ticker]["total_invested"]
                new_cost = old_cost - cost_to_subtract
                logger.debug(f"DEMERGER {ticker}: {old_cost}->{new_cost}")
                holdings_state[ticker]["total_invested"] = new_cost

        elif tx.transaction_type == "SELL":
            if holdings_state[ticker]["quantity"] > 0:
                logger.debug(
                    f"Processing SELL tx {tx.id} for {ticker}. "
                    f"Details: {tx.details}"
                )

                realized_pnl_for_sale = Decimal(0)
                cost_of_shares_sold = Decimal(0)
                sold_qty = tx.quantity

                # Check for specific lot links
                links = sell_links_map.get(tx.id, [])

                fx_rate = (
                    Decimal(str(tx.details.get("fx_rate", 1)))
                    if tx.details
                    else Decimal(1)
                )

                if links:
                    for link in links:
                        buy_tx = tx_map.get(link.buy_transaction_id)
                        # Fallback for buy_tx finding (safe-guard)
                        if not buy_tx:
                             buy_tx = db.query(models.Transaction).get(
                                 link.buy_transaction_id
                             )

                        if buy_tx:
                            buy_price = buy_tx.price_per_unit
                            # Get buy transaction's FX rate to convert to INR
                            buy_fx_rate = (
                                Decimal(str(buy_tx.details.get("fx_rate", 1)))
                                if buy_tx.details else Decimal(1)
                            )
                            buy_price_inr = buy_price * buy_fx_rate

                            # Calculate P&L: both sell and buy in INR
                            pnl = (
                                (tx.price_per_unit * fx_rate) - buy_price_inr
                            ) * link.quantity
                            realized_pnl_for_sale += pnl

                            # Cost is in INR (matches total_invested)
                            cost_of_shares_sold += buy_price_inr * link.quantity
                            sold_qty -= link.quantity

                            logger.debug(
                                "Linked Sell: qty=%s, sell=%s, buy=%s, PnL=%s",
                                link.quantity,
                                tx.price_per_unit,
                                buy_price,
                                pnl
                            )

                if sold_qty > 0:
                     avg_buy_price = (
                        holdings_state[ticker]["total_invested"]
                        / holdings_state[ticker]["quantity"]
                    )
                     # For foreign stocks, the sale price must be converted to INR
                     pnl = (
                        (tx.price_per_unit * fx_rate) - avg_buy_price
                     ) * sold_qty
                     realized_pnl_for_sale += pnl
                     cost_of_shares_sold += avg_buy_price * sold_qty

                     logger.debug(
                        "Unlinked Sell: Sold %s @ %s, Avg Cost @ %s. PnL: %s",
                        sold_qty,
                        tx.price_per_unit,
                        avg_buy_price,
                        pnl
                    )
                total_realized_pnl += realized_pnl_for_sale
                holdings_state[ticker]["realized_pnl"] += realized_pnl_for_sale

                # Reduce the total invested amount by the cost basis of the shares sold
                holdings_state[ticker]["total_invested"] -= cost_of_shares_sold
                holdings_state[ticker]["quantity"] -= tx.quantity

    current_holdings_tickers = [
        ticker for ticker, data in holdings_state.items() if data["quantity"] > 0
    ]

    assets_to_price = [
        {
            "ticker_symbol": ticker,
            "exchange": next((
                a.exchange for a in asset_map.values()
                if a.ticker_symbol == ticker
            ), None),
            "asset_type": next((
                a.asset_type
                for a in asset_map.values()
                if a.ticker_symbol == ticker
            ), None),
        }
        for ticker in current_holdings_tickers
    ]

    price_details = (
        financial_data_service.get_current_prices(assets_to_price)
        if assets_to_price
        else {}
    )

    # --- On-demand enrichment for assets with NULL sector ---
    # This enriches sector/industry/country when fetching portfolio
    needs_commit = False
    for ticker in current_holdings_tickers:
        asset = next(
            (a for a in asset_map.values() if a.ticker_symbol == ticker), None
        )
        if asset and asset.sector is None:
            asset_type_upper = (asset.asset_type or "").upper()
            if asset_type_upper in ["STOCK", "ETF"]:
                # Equities: enrich via yfinance
                enrichment = (
                    financial_data_service.yfinance_provider.get_enrichment_data(
                        ticker, asset.exchange
                    )
                )
                if enrichment:
                    asset.sector = enrichment.get("sector")
                    asset.industry = enrichment.get("industry")
                    asset.country = enrichment.get("country")
                    asset.market_cap = enrichment.get("market_cap")
                    asset.investment_style = enrichment.get("investment_style")
                    db.add(asset)
                    needs_commit = True
            elif asset.asset_type in ["MUTUAL_FUND", "MUTUAL FUND", "Mutual Fund"]:
                # Mutual Funds: enrich via AMFI
                nav_data = financial_data_service.amfi_provider.get_all_nav_data()
                fund_data = nav_data.get(ticker, {})
                mf_category = fund_data.get("mf_category")
                mf_sub_category = fund_data.get("mf_sub_category")
                if mf_category:
                    asset.sector = mf_category
                    asset.industry = mf_sub_category
                    # FoF Overseas are international funds
                    if mf_sub_category and "overseas" in mf_sub_category.lower():
                        asset.country = "International"
                    else:
                        asset.country = "India"
                    db.add(asset)
                    needs_commit = True
    if needs_commit:
        try:
            db.commit()
        except Exception as e:
            # Just log - don't rollback as it would delete session objects
            logger.warning(f"Failed to commit enrichment data: {e}")
            # Expire modified objects to reload from DB
            for ticker in current_holdings_tickers:
                asset = next(
                    (a for a in asset_map.values() if a.ticker_symbol == ticker),
                    None
                )
                if asset:
                    db.expire(asset)

    # --- Pre-fetch FX rates for foreign assets ---
    currencies_needed = set()
    for ticker in current_holdings_tickers:
        asset = next((a for a in asset_map.values() if a.ticker_symbol == ticker), None)
        if asset and asset.currency and asset.currency != "INR":
            currencies_needed.add(asset.currency)

    fx_rates = {}
    if currencies_needed:
        fx_assets_to_fetch = [
            {
                "ticker_symbol": f"{currency}INR=X",
                "asset_type": "Currency",
                "exchange": None
            }
            for currency in currencies_needed
        ]
        fx_prices = financial_data_service.get_current_prices(fx_assets_to_fetch)
        for currency in currencies_needed:
            ticker = f"{currency}INR=X"
            if ticker in fx_prices:
                fx_rates[currency] = fx_prices[ticker]["current_price"]
            else:
                logger.warning(f"Could not fetch FX rate for {currency}")
                fx_rates[currency] = Decimal(1)

    for ticker in current_holdings_tickers:
        asset = next((a for a in asset_map.values() if a.ticker_symbol == ticker), None)
        data = holdings_state[ticker]
        price_info = price_details.get(
            ticker, {"current_price": Decimal(0), "previous_close": Decimal(0)}
        )

        quantity = data["quantity"]
        total_invested = data["total_invested"]

        days_pnl = Decimal("0.0")
        if asset.asset_type == "BOND" and asset.bond:
            bond_details = asset.bond
            current_price = Decimal(str(price_info["current_price"]))

            if current_price == 0 and asset.ticker_symbol:
                yf_price = financial_data_service.get_price_from_yfinance(
                    asset.ticker_symbol
                )
                if yf_price:
                    current_price = yf_price

            if current_price == 0 and bond_details.bond_type == BondType.TBILL:
                first_buy = min(
                    (
                        tx
                        for tx in transactions
                        if tx.asset_id == asset.id and tx.transaction_type == "BUY"
                    ),
                    key=lambda x: x.transaction_date,
                    default=None,
                )
                if first_buy and bond_details.face_value:
                    purchase_date = first_buy.transaction_date.date()
                    total_days = (bond_details.maturity_date - purchase_date).days
                    days_elapsed = (date.today() - purchase_date).days
                    if total_days > 0 and days_elapsed > 0:
                        price_increase = (
                            Decimal(str(bond_details.face_value))
                            - first_buy.price_per_unit
                        ) * (Decimal(days_elapsed) / Decimal(total_days))
                        current_price = first_buy.price_per_unit + price_increase

            if current_price == 0:
                current_price = (
                    total_invested / quantity if quantity > 0 else Decimal(0)
                )
                price_info["previous_close"] = current_price.quantize(Decimal("0.01"))
        else:
            current_price = Decimal(str(price_info["current_price"]))

        previous_close = Decimal(str(price_info["previous_close"]))
        average_buy_price = total_invested / quantity if quantity > 0 else Decimal(0)
        days_pnl = (current_price - previous_close) * quantity
        days_pnl_percentage = (
            float((current_price - previous_close) / previous_close)
            if previous_close > 0
            else 0.0
        )
        current_value = quantity * current_price

        # --- FX Conversion for Current Value ---
        # If the asset is not in INR, its current value must be converted
        # using the REAL-TIME rate.
        if asset.currency != "INR":
            # 1. Convert current value using real-time FX rate
            live_fx_rate = fx_rates.get(asset.currency, Decimal(1))
            current_value_inr = current_value * live_fx_rate

            # 2. Convert days_pnl using real-time FX rate
            # days_pnl is (current_price - prev_close) * qty * fx_rate
            # Note: We approximate by applying today's FX rate to the
            # change in asset currency.
            days_pnl_inr = days_pnl * live_fx_rate

            current_value = current_value_inr
            days_pnl = days_pnl_inr

        holdings_list.append(
            schemas.Holding(
                asset_id=asset.id,
                ticker_symbol=ticker,
                asset_name=asset.name,
                asset_type=asset.asset_type,
                currency=asset.currency, # This is the currency of the asset's price
                group="EQUITIES",  # Placeholder, will be set properly later
                quantity=quantity,
                average_buy_price=average_buy_price,
                total_invested_amount=total_invested,
                current_price=current_price,
                current_value=current_value,
                days_pnl=days_pnl,
                days_pnl_percentage=days_pnl_percentage,
                unrealized_pnl=Decimal("0.0"),
                realized_pnl=data.get("realized_pnl", Decimal("0.0")),
                unrealized_pnl_percentage=0.0,
                investment_style=asset.investment_style,
                bond=asset.bond,
            )
        )

    if settings.DEBUG:
        logger.debug("--- Market Traded Holdings ---")
        for h in holdings_list:
            logger.debug(h.model_dump_json(indent=2))
        logger.debug("------------------------------")

    return holdings_list, total_realized_pnl


class CRUDHolding:
    """
    CRUD operations for portfolio holdings.
    This is a read-only CRUD module that calculates holdings based on transactions.
    """

    @cache_analytics_data(
        prefix="analytics:portfolio_holdings_and_summary",
        arg_names=["portfolio_id"],
        response_model=schemas.PortfolioHoldingsAndSummary,
    )
    def get_portfolio_holdings_and_summary(
        self, db: Session, *, portfolio_id: uuid.UUID
    ) -> schemas.PortfolioHoldingsAndSummary:
        """Calculates the consolidated holdings and a summary for a given portfolio."""
        start_time = time.time()
        logger.info(
            f"Starting holdings calculation for portfolio_id: {portfolio_id}"
        )
        transactions = crud.transaction.get_multi_by_portfolio(
            db=db, portfolio_id=portfolio_id
        )
        all_fixed_deposits = crud.fixed_deposit.get_multi_by_portfolio(
            db, portfolio_id=portfolio_id
        )
        all_recurring_deposits = crud.recurring_deposit.get_multi_by_portfolio(
            db=db, portfolio_id=portfolio_id
        )

        # --- Process Market-Traded Assets First ---
        market_traded_holdings, total_realized_pnl = _process_market_traded_assets(
            db, portfolio_id, transactions, Decimal("0.0")
        )
        logger.info(
            f"Processed {len(market_traded_holdings)} market-traded assets. "
            f"Realized PNL from sales: {total_realized_pnl}"
        )
        holdings_list: List[schemas.Holding] = market_traded_holdings

        # --- Process Non-Market-Traded Assets (FDs, RDs, PPF) ---
        fd_holdings, pnl_from_matured_fds = _process_fixed_deposits(all_fixed_deposits)
        rd_holdings, pnl_from_matured_rds = _process_recurring_deposits(
            all_recurring_deposits
        )
        logger.info(
            "Processed FDs (%s), RDs (%s).", len(fd_holdings), len(rd_holdings)
        )
        logger.info(
            "Realized PNL from matured FDs: %s, RDs: %s",
            pnl_from_matured_fds,
            pnl_from_matured_rds,
        )
        holdings_list.extend(fd_holdings)
        holdings_list.extend(rd_holdings)
        total_realized_pnl += pnl_from_matured_fds + pnl_from_matured_rds
        all_portfolio_assets = crud.asset.get_multi_by_portfolio(
            db, portfolio_id=portfolio_id
        )
        ppf_assets = [
            asset for asset in all_portfolio_assets if asset.asset_type.upper() == "PPF"
        ]
        logger.info(f"Found {len(ppf_assets)} PPF assets to process.")
        # --- PPF Holdings ---
        for ppf_asset in ppf_assets:
            # Lock the asset row before processing to prevent race conditions
            # on the interest calculation logic, which has a write side-effect.
            # This is only supported by PostgreSQL.
            db.query(models.Asset).filter_by(id=ppf_asset.id).with_for_update().first()
            logger.info(f"Processing PPF asset {ppf_asset.id}...")
            ppf_holding = process_ppf_holding(db, ppf_asset, portfolio_id)
            if ppf_holding:
                holdings_list.append(ppf_holding)
                if ppf_holding.realized_pnl:
                    logger.debug(
                        "  - PPF Holding Realized PNL: %s", ppf_holding.realized_pnl
                    )

        logger.info("Finished processing all PPF assets.")

        # --- Final Grouping and Summary Calculation ---
        logger.info(
            f"Starting final summary. Total holdings in list: {len(holdings_list)}"
        )
        for holding_item in holdings_list:
            group_map = {
                "STOCK": "EQUITIES",
                "Mutual Fund": "EQUITIES",
                "MUTUAL_FUND": "EQUITIES",
                "ETF": "EQUITIES",
                "FIXED_DEPOSIT": "DEPOSITS",
                "RECURRING_DEPOSIT": "DEPOSITS",
                "BOND": "BONDS",
                "PPF": "GOVERNMENT_SCHEMES",
            }
            group_map_upper = {k.upper(): v for k, v in group_map.items()}
            holding_item.group = group_map_upper.get(
                str(holding_item.asset_type).upper(), "MISCELLANEOUS")

        # --- Calculate Unrealized P&L for all holdings ---
        # This must be done after all holdings are aggregated.
        for holding in holdings_list:
            if holding.asset_type not in ["FIXED_DEPOSIT", "RECURRING_DEPOSIT", "PPF"]:
                # For market-traded assets, it's current value minus cost basis
                unrealized_pnl = holding.current_value - holding.total_invested_amount
            else:
                # For deposits/PPF, it's already calculated
                unrealized_pnl = holding.unrealized_pnl

            holding.unrealized_pnl = unrealized_pnl
            if holding.total_invested_amount > 0:
                holding.unrealized_pnl_percentage = float(
                    unrealized_pnl / holding.total_invested_amount
                )

        summary = _calculate_summary(holdings_list, total_realized_pnl, transactions)
        logger.info(
            f"Calculation complete. Total portfolio value: {summary.total_value}"
        )
        logger.debug(
            "[_get_portfolio_holdings_and_summary] Final summary object: %s", summary
        )
        end_time = time.time()
        logger.info(
            f"Holdings calculation for portfolio {portfolio_id} "
            f"took {end_time - start_time:.4f} seconds."
        )

        return schemas.PortfolioHoldingsAndSummary(
            summary=summary, holdings=holdings_list
        )


holding = CRUDHolding()
