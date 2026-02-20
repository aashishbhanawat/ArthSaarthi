"""
Schedule FA (Foreign Assets) Service

Generates data for ITR-2/ITR-3 Schedule FA (Foreign Assets) reporting.
Uses CALENDAR YEAR (Jan 1 - Dec 31 of AY-2) not Financial Year.

Example: For AY 2025-26, report assets held Jan 1, 2024 to Dec 31, 2024.
"""
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from app.models import Asset, Transaction
from app.schemas.enums import TransactionType
from app.services.providers.yfinance_provider import YFinanceProvider

logger = logging.getLogger(__name__)


class ScheduleFAEntry:
    """Entry for Schedule FA A3 (Foreign Equity & Debt)"""
    def __init__(
        self,
        country_code: str,
        country_name: str,
        entity_name: str,
        entity_address: str,
        zip_code: str,
        nature_of_entity: str,
        date_acquired: date,
        initial_value: Decimal,
        peak_value: Decimal,
        closing_value: Decimal,
        gross_amount_received: Decimal,
        gross_proceeds_from_sale: Decimal,
        currency: str,
        asset_ticker: str,
        quantity_held: Decimal,
    ):
        self.country_code = country_code
        self.country_name = country_name
        self.entity_name = entity_name
        self.entity_address = entity_address
        self.zip_code = zip_code
        self.nature_of_entity = nature_of_entity
        self.date_acquired = date_acquired
        self.initial_value = initial_value
        self.peak_value = peak_value
        self.closing_value = closing_value
        self.gross_amount_received = gross_amount_received
        self.gross_proceeds_from_sale = gross_proceeds_from_sale
        self.currency = currency
        self.asset_ticker = asset_ticker
        self.quantity_held = quantity_held


class ScheduleFAService:
    def __init__(self, db: Session):
        self.db = db
        self.yf_provider = YFinanceProvider(cache_client=None)

    def get_schedule_fa(
        self,
        user_id: str,
        calendar_year: int,  # e.g., 2024 for AY 2025-26
        portfolio_id: Optional[str] = None
    ) -> List[dict]:
        """
        Generate Schedule FA A3 data for a calendar year.

        IMPORTANT: Each BUY lot is a separate entry (per ITR requirements).

        Args:
            calendar_year: The calendar year to report (Jan 1 - Dec 31)
        """
        start_date = datetime(calendar_year, 1, 1)
        end_date = datetime(calendar_year, 12, 31, 23, 59, 59)

        # Get all buy lots for foreign assets
        lots = self._get_foreign_lots_for_period(
            user_id, start_date, end_date, portfolio_id
        )

        # Fetch historical prices from Yahoo for peak/closing value
        price_data = self._fetch_historical_prices_for_lots(
            lots, start_date.date(), end_date.date()
        )

        entries = []
        for lot in lots:
            asset = lot["asset"]
            buy_tx = lot["buy_transaction"]
            ticker = asset.ticker_symbol
            asset_prices = price_data.get(ticker, {})

            # Calculate values for this specific lot
            initial_value = self._calculate_lot_initial_value(
                lot, start_date, asset_prices
            )
            peak_value, peak_date = self._calculate_lot_peak_value(
                lot, start_date, end_date, asset_prices
            )
            closing_value = self._calculate_lot_closing_value(
                lot, end_date, asset_prices
            )
            gross_proceeds = lot["gross_proceeds"]  # Calculated during lot extraction
            gross_received = lot["dividends"]  # Placeholder until dividend tracking

            # Country info
            country_code, country_name = self._get_country_info(asset)

            # Round values to 2 decimal places
            entries.append({
                "country_code": country_code,
                "country_name": country_name,
                "entity_name": asset.name,
                "entity_address": "",  # Not stored in system
                "zip_code": "",
                "nature_of_entity": self._get_entity_nature(asset),
                "date_acquired": buy_tx.transaction_date.date(),
                "initial_value": round(float(initial_value), 2),
                "peak_value": round(float(peak_value), 2),
                "peak_value_date": peak_date,
                "closing_value": round(float(closing_value), 2),
                "gross_amount_received": round(float(gross_received), 2),
                "gross_proceeds_from_sale": round(float(gross_proceeds), 2),
                "currency": asset.currency,
                "asset_ticker": asset.ticker_symbol,
                "quantity_held": round(float(lot["quantity_remaining"]), 4),
            })

        return entries

    def _get_foreign_lots_for_period(
        self, user_id: str, start_date: datetime, end_date: datetime,
        portfolio_id: Optional[str]
    ) -> List[dict]:
        """
        Get all foreign lots held during the period with detailed disposal tracking.
        Uses Replay logic (Links + FIFO fallback) to track accurate balances.
        """
        # Fetch ALL foreign transactions (Buys and Sells) sorted by date
        query = (
            self.db.query(Transaction)
            .join(Asset)
            .options(joinedload(Transaction.sell_links))
            .filter(
                Transaction.user_id == user_id,
                Asset.currency != "INR",
                Asset.currency.isnot(None),
                Transaction.transaction_type.in_([
                    TransactionType.BUY, TransactionType.RSU_VEST,
                    TransactionType.ESPP_PURCHASE, TransactionType.BONUS,
                    TransactionType.SELL
                ])
            )
        )
        if portfolio_id:
            query = query.filter(Transaction.portfolio_id == portfolio_id)

        all_txs = query.order_by(Transaction.transaction_date).all()

        # Track lots: {buy_id: {
        # 'buy_tx': tx, 'initial_qty': qty, 'current_qty': qty, 'disposals': [(d,q)]
        # }}
        lots_map = {}

        for tx in all_txs:
            # Use IST adjustment for dates
            tx_date_ist = tx.transaction_date + timedelta(hours=5, minutes=30)

            if tx.transaction_type in [
                TransactionType.BUY, TransactionType.RSU_VEST,
                TransactionType.ESPP_PURCHASE, TransactionType.BONUS
            ]:
                lots_map[tx.id] = {
                    "asset": tx.asset,
                    "buy_transaction": tx,
                    "initial_qty": tx.quantity,
                    "current_qty": tx.quantity,
                    "disposals": [],
                    "gross_proceeds": Decimal(0)
                }

            elif tx.transaction_type == TransactionType.SELL:
                qty_to_sell = tx.quantity

                # 1. Process Links first
                if tx.sell_links:
                    for link in tx.sell_links:
                        if link.buy_transaction_id in lots_map:
                            lot = lots_map[link.buy_transaction_id]
                            take = link.quantity

                            # Deduct
                            if lot["current_qty"] >= take: # Should usually match
                                lot["current_qty"] -= take
                                lot["disposals"].append({
                                    "date": tx_date_ist, "qty": take
                                })
                                qty_to_sell -= take

                                # Track proceeds if in reporting period
                                if start_date <= tx_date_ist <= end_date:
                                    lot["gross_proceeds"] += take * tx.price_per_unit

                # 2. FIFO Fallback for remaining unlinked quantity
                if qty_to_sell > 0.000001:
                    # Sort active lots by buy date
                    active_lots = sorted(
                        [
                            lot for lot in lots_map.values()
                            if lot["current_qty"] > 0
                            and lot["asset"].id == tx.asset_id
                        ],
                        key=lambda x: x["buy_transaction"].transaction_date
                    )

                    for lot in active_lots:
                        if qty_to_sell <= 0.000001:
                            break

                        take = min(lot["current_qty"], qty_to_sell)
                        lot["current_qty"] -= take
                        lot["disposals"].append({"date": tx_date_ist, "qty": take})
                        qty_to_sell -= take

                        if start_date <= tx_date_ist <= end_date:
                            lot["gross_proceeds"] += take * tx.price_per_unit

        # Filter Lots valid for this period
        # Valid if: (Held at start) OR (Acquired during period)
        # Held at start: Acquired < Start AND Not fully sold before Start
        # Acquired during: Start <= Acquired <= End

        final_lots = []
        for lot in lots_map.values():
            buy_date_ist = lot["buy_transaction"].transaction_date + timedelta(
                hours=5, minutes=30
            )

            # Reconstruct Quantity at Start
            qty_at_start = lot["initial_qty"]
            for d in lot["disposals"]:
                if d["date"] < start_date:
                    qty_at_start -= d["qty"]
            qty_at_start = max(Decimal(0), qty_at_start)

            # Reconstruct Quantity at End (current_qty from replay matches end state?
            # Yes, if replay includes all history)
            # But we need check if any disposals happened AFTER end_date
            # (not possible if query restricted?
            # Wait, we queried ALL txs? No, we need ALL history to replay correctly.
            # But the query filters? The query logic uses user_id generally.
            # If query is filtered by date, replay is broken.
            # My query above does NOT filter by date. It gets all transactions. Good.

            # Calculate Qty at End of Period
            qty_at_end = lot["initial_qty"]
            for d in lot["disposals"]:
                if d["date"] <= end_date:
                    qty_at_end -= d["qty"]
            qty_at_end = max(Decimal(0), qty_at_end)

            acquired_during = start_date <= buy_date_ist <= end_date
            held_at_start = buy_date_ist < start_date and qty_at_start > 0

            if acquired_during or held_at_start:
                 final_lots.append({
                     "asset": lot["asset"],
                     "buy_transaction": lot["buy_transaction"],
                     "quantity_at_start": qty_at_start,
                     "quantity_remaining": qty_at_end, # "Closing Balance"
                     "gross_proceeds": lot["gross_proceeds"],
                     "disposals": lot["disposals"], # needed for Peak Value
                     "dividends": Decimal(0)
                 })

        return final_lots


    def _fetch_historical_prices_for_lots(
        self, lots: List[dict], start_date: date, end_date: date
    ) -> Dict[str, Dict[date, Decimal]]:
        """
        Fetch historical prices from Yahoo Finance for all foreign assets in lots.
        """
        # Deduplicate assets
        seen_tickers = set()
        assets_for_yf = []
        for lot in lots:
            asset = lot["asset"]
            if asset.ticker_symbol not in seen_tickers:
                seen_tickers.add(asset.ticker_symbol)
                assets_for_yf.append({
                    "ticker_symbol": asset.ticker_symbol,
                    "exchange": asset.exchange,
                })

        if not assets_for_yf:
            return {}

        try:
            prices = self.yf_provider.get_historical_prices(
                assets_for_yf, start_date, end_date
            )
            logger.debug(f"Fetched Yahoo prices for {len(prices)} assets")
            return prices
        except Exception as e:
            logger.warning(f"Failed to fetch Yahoo prices for Schedule FA: {e}")
            return {}

    def _calculate_lot_initial_value(
        self, lot: dict, start_date: datetime, yahoo_prices: Dict[date, Decimal]
    ) -> Decimal:
        """
        Initial value of the investment.
        For Schedule FA, this is the Cost of Acquisition (Historical Cost).
        It is NOT the market value at the start of the year.

        For ESPP/RSU, this should be the FMV at the time of acquisition
        (which is our cost basis).
        """

        # If the lot was fully acquired *after* start of year, the initial investment
        # for reporting purposes is still the cost of that lot.
        # Actually, if we are reporting "Initial Value of investment", it is ALWAYS
        # the cost of acquisition, regardless of when it was bought
        # (as long as it's held during the year).

        # However, `quantity_at_start` in our lot dict refers to "qty held on Jan 1".
        # But for the "Initial Value" column in ITR, we want the cost of the *entire*
        # lot that contributes to this entry?
        # The user's request implies per-lot reporting.
        # So we should report the cost of the *original* quantity of this lot?
        # Or the cost of the quantity that was held during the period?

        # "Initial value of the investment":
        # Usually means the original cost of the holding.
        # If we sold part of it in previous years, do we report the full original cost?
        # ITR instructions say "Initial value of investment".
        # Let's use the Cost of Acquisition for the quantity related to this lot logic.

        # Our `lots` logic breaks down holdings. `lot["buy_transaction"]` is the source.
        # `lot["quantity_at_start"]` is what we had on Jan 1.
        # `lot["quantity_remaining"]` is what we have on Dec 31.

        # If we iterate per BUY transaction (which we do now),
        # then "Initial value" should likely be the total cost of that BUY transaction?
        # Or just the cost of the portion relevant to this year?
        # Usually, Schedule FA asks for the investment details.

        # Current logic checks `quantity_at_start`.
        # If we bought it mid-year, qty_at_start is 0.
        # This causes the issue.
        # We should use the `buy_transaction` quantity if we want the full lot cost,
        # OR better: The cost of the quantity that justifies this entry.

        # Let's assume we report the cost of the share counts we are tracking.
        # Since we split by lot, the "Investment" is this specific lot.
        # Value = Price * Quantity.

        buy_tx = lot["buy_transaction"]
        buy_price = buy_tx.price_per_unit

        # Use FMV for ESPP/RSU if available (same logic as Capital Gains)
        if (buy_tx.transaction_type in [
            TransactionType.ESPP_PURCHASE, TransactionType.RSU_VEST
        ] and buy_tx.details and "fmv" in buy_tx.details):
             buy_price = Decimal(str(buy_tx.details["fmv"]))

        # For the "Initial Value" field:
        # If it's a lot held from previous years, it's the cost of that lot.
        # If it's acquired this year, it's the cost of acquisition.
        # So it's always Buy Price * Quantity.

        # WHICH Quantity?
        # If we sold 50% last year, do we report 100% of cost or 50%?
        # Schedule FA usually tracks the *current* holding's history.
        # If we use original buy quantity, it might be misleading if we only
        # hold a fraction.
        # BUT, if we use only remaining qty, it might look like a smaller investment.
        # However, Peak Value uses max holding.
        # Let's use the Max Quantity held during the period for the "Investment Value".
        # i.e. The cost basis of the maximum shares we held this year.

        max_qty = max(lot["quantity_at_start"], lot["quantity_remaining"])
        if buy_tx.transaction_date >= start_date:
            max_qty = buy_tx.quantity # Acquired this year, so max is what we bought

        return max_qty * buy_price

    def _calculate_lot_peak_value(
        self, lot: dict, start_date: datetime, end_date: datetime,
        yahoo_prices: Dict[date, Decimal]
    ) -> Tuple[Decimal, Optional[date]]:
        """
        Peak value of this lot during the calendar year.
        Calculates Max(Qty_on_Day * Price_on_Day) for the year.
        Returns (Max Value, Date of Max Value).
        """
        buy_tx = lot["buy_transaction"]
        buy_date = buy_tx.transaction_date.date()
        s_date = start_date.date()
        e_date = end_date.date()

        # 1. Identify critical dates (boundaries + disposals) in chronological order
        critical_dates = {s_date, e_date}
        if s_date <= buy_date <= e_date:
            critical_dates.add(buy_date)

        disposals = sorted(
            [d for d in lot["disposals"] if s_date <= d["date"].date() <= e_date],
            key=lambda x: x["date"]
        )
        for d in disposals:
            d_date = d["date"].date()
            critical_dates.add(d_date)
            # Add next day to start a new interval with reduced quantity
            if d_date < e_date:
                critical_dates.add(d_date + timedelta(days=1))

        sorted_dates = sorted(list(critical_dates))

        # 2. Iterate intervals
        global_peak = Decimal(0)
        global_peak_date = None

        # Helper to get qty on date
        def get_qty_on_date(d: date):
            if d < buy_date:
                return Decimal(0)
            q = lot["buy_transaction"].quantity  # Start with full lot
            return q - sum(
                disp["qty"] for disp in lot["disposals"] if disp["date"].date() < d
            )

        current_idx = 0
        while sorted_dates[current_idx] < e_date:
            seg_start = sorted_dates[current_idx]
            if current_idx + 1 < len(sorted_dates):
                seg_end = sorted_dates[current_idx + 1]
            else:
                seg_end = e_date

            qty = get_qty_on_date(seg_start)

            if qty > 0:
                # Find max price in range [seg_start, seg_end]
                max_p = Decimal(0)
                max_p_date = seg_start # Fallback

                if yahoo_prices:
                    curr = seg_start
                    while curr <= seg_end and curr <= e_date:
                        p = yahoo_prices.get(curr, Decimal(0))
                        if p > max_p:
                            max_p = p
                            max_p_date = curr
                        curr += timedelta(days=1)

                if max_p == 0:
                    max_p = buy_tx.price_per_unit
                    max_p_date = seg_start # Use start of interval if flat price

                val = qty * max_p
                if val > global_peak:
                    global_peak = val
                    global_peak_date = max_p_date

            current_idx += 1
            if current_idx >= len(sorted_dates):
                break

        return global_peak, global_peak_date

    def _calculate_lot_closing_value(
        self, lot: dict, end_date: datetime, yahoo_prices: Dict[date, Decimal]
    ) -> Decimal:
        """
        Closing value of this lot at Dec 31.
        Uses Yahoo price for Dec 31 (or nearest) * remaining quantity.
        """
        qty = lot["quantity_remaining"]
        if qty <= 0:
            return Decimal(0)

        buy_tx = lot["buy_transaction"]

        # Try to get Dec 31 price from Yahoo
        if yahoo_prices:
            sorted_dates = sorted(yahoo_prices.keys(), reverse=True)
            if sorted_dates:
                return qty * yahoo_prices[sorted_dates[0]]

        # Fallback to buy price
        return qty * buy_tx.price_per_unit

    def _fetch_historical_prices(
        self, holdings: List[dict], start_date: date, end_date: date
    ) -> Dict[str, Dict[date, Decimal]]:
        """
        Fetch historical prices from Yahoo Finance for all foreign assets.
        """
        assets_for_yf = []
        for holding in holdings:
            asset = holding["asset"]
            assets_for_yf.append({
                "ticker_symbol": asset.ticker_symbol,
                "exchange": asset.exchange,
            })

        if not assets_for_yf:
            return {}

        try:
            prices = self.yf_provider.get_historical_prices(
                assets_for_yf, start_date, end_date
            )
            logger.debug(f"Fetched Yahoo prices for {len(prices)} assets")
            return prices
        except Exception as e:
            logger.warning(f"Failed to fetch Yahoo prices for Schedule FA: {e}")
            return {}

    def _get_foreign_holdings_for_period(
        self, user_id: str, start_date: datetime, end_date: datetime,
        portfolio_id: Optional[str]
    ) -> List[dict]:
        """
        Find all foreign assets user held at any point during the period.
        """
        # Get all transactions for foreign assets in the period
        query = (
            self.db.query(Transaction)
            .join(Asset)
            .filter(
                Transaction.user_id == user_id,
                Asset.currency != "INR",
                Asset.currency.isnot(None),
            )
        )

        if portfolio_id:
            query = query.filter(Transaction.portfolio_id == portfolio_id)

        all_transactions = query.order_by(Transaction.transaction_date).all()

        # Group by asset and calculate holdings
        asset_holdings = {}
        for tx in all_transactions:
            asset_id = str(tx.asset_id)
            if asset_id not in asset_holdings:
                asset_holdings[asset_id] = {
                    "asset": tx.asset,
                    "transactions": [],
                    "first_buy_date": None,
                    "quantity_at_start": Decimal(0),
                    "quantity_at_end": Decimal(0),
                }
            asset_holdings[asset_id]["transactions"].append(tx)

            # Track first buy date
            if tx.transaction_type in [
                TransactionType.BUY, TransactionType.RSU_VEST,
                TransactionType.ESPP_PURCHASE
            ]:
                if asset_holdings[asset_id]["first_buy_date"] is None:
                    asset_holdings[asset_id]["first_buy_date"] = (
                        tx.transaction_date.date()
                    )

        # Calculate quantity at start and end of period
        for asset_id, holding in asset_holdings.items():
            qty_at_start = Decimal(0)
            qty_at_end = Decimal(0)

            for tx in holding["transactions"]:
                if tx.transaction_type in [
                    TransactionType.BUY, TransactionType.RSU_VEST,
                    TransactionType.ESPP_PURCHASE, TransactionType.BONUS
                ]:
                    if tx.transaction_date < start_date:
                        qty_at_start += tx.quantity
                    if tx.transaction_date <= end_date:
                        qty_at_end += tx.quantity
                elif tx.transaction_type == TransactionType.SELL:
                    if tx.transaction_date < start_date:
                        qty_at_start -= tx.quantity
                    if tx.transaction_date <= end_date:
                        qty_at_end -= tx.quantity

            holding["quantity_at_start"] = max(Decimal(0), qty_at_start)
            holding["quantity_at_end"] = max(Decimal(0), qty_at_end)

        # Filter to only assets held during the period
        held_during_period = [
            h for h in asset_holdings.values()
            if h["quantity_at_start"] > 0 or h["quantity_at_end"] > 0
            or any(
                start_date <= tx.transaction_date <= end_date
                for tx in h["transactions"]
            )
        ]

        return held_during_period

    def _calculate_initial_value(
        self, holding: dict, start_date: datetime
    ) -> Decimal:
        """Value of holding at start of calendar year"""
        qty = holding["quantity_at_start"]
        if qty <= 0:
            return Decimal(0)

        # Use average cost basis
        total_cost = Decimal(0)
        total_qty = Decimal(0)
        for tx in holding["transactions"]:
            if tx.transaction_date >= start_date:
                break
            if tx.transaction_type in [
                TransactionType.BUY, TransactionType.RSU_VEST,
                TransactionType.ESPP_PURCHASE
            ]:
                total_cost += tx.quantity * tx.price_per_unit
                total_qty += tx.quantity

        if total_qty > 0:
            avg_price = total_cost / total_qty
            return qty * avg_price
        return Decimal(0)

    def _calculate_peak_value(
        self, holding: dict, asset: Asset, start_date: datetime, end_date: datetime,
        yahoo_prices: Dict[date, Decimal]
    ) -> Decimal:
        """
        Peak value during the calendar year.
        Uses max quantity held * highest price from Yahoo Finance.
        """
        # Get max quantity held during period
        max_qty = holding["quantity_at_start"]
        current_qty = holding["quantity_at_start"]

        for tx in holding["transactions"]:
            if tx.transaction_date < start_date:
                continue
            if tx.transaction_date > end_date:
                break

            if tx.transaction_type in [
                TransactionType.BUY, TransactionType.RSU_VEST,
                TransactionType.ESPP_PURCHASE, TransactionType.BONUS
            ]:
                current_qty += tx.quantity
            elif tx.transaction_type == TransactionType.SELL:
                current_qty -= tx.quantity

            max_qty = max(max_qty, current_qty)

        # Get highest price from Yahoo data
        max_price = Decimal(0)
        if yahoo_prices:
            max_price = max(yahoo_prices.values())
            logger.debug(f"Yahoo peak price for {asset.ticker_symbol}: {max_price}")

        # Fallback to transaction prices if no Yahoo data
        if max_price == 0:
            for tx in holding["transactions"]:
                if start_date <= tx.transaction_date <= end_date:
                    if tx.price_per_unit > max_price:
                        max_price = tx.price_per_unit

            if max_price == 0 and holding["transactions"]:
                max_price = holding["transactions"][-1].price_per_unit

        return max_qty * max_price if max_price > 0 else Decimal(0)

    def _calculate_closing_value(
        self, holding: dict, asset: Asset, end_date: datetime,
        yahoo_prices: Dict[date, Decimal]
    ) -> Decimal:
        """
        Value at end of calendar year (Dec 31).
        Uses Yahoo Finance price for Dec 31 (or nearest available).
        """
        qty = holding["quantity_at_end"]
        if qty <= 0:
            return Decimal(0)

        closing_price = Decimal(0)

        # Try to get Dec 31 price from Yahoo data
        if yahoo_prices:
            # Get the last available price (closest to Dec 31)
            sorted_dates = sorted(yahoo_prices.keys(), reverse=True)
            if sorted_dates:
                closing_price = yahoo_prices[sorted_dates[0]]
                logger.debug(
                    f"Yahoo closing price for {asset.ticker_symbol} "
                    f"on {sorted_dates[0]}: {closing_price}"
                )

        # Fallback to last transaction price
        if closing_price == 0:
            for tx in reversed(holding["transactions"]):
                if tx.transaction_date <= end_date:
                    closing_price = tx.price_per_unit
                    break

        return qty * closing_price

    def _calculate_gross_proceeds(
        self, holding: dict, start_date: datetime, end_date: datetime
    ) -> Decimal:
        """Total sale proceeds during the calendar year"""
        total = Decimal(0)
        for tx in holding["transactions"]:
            if start_date <= tx.transaction_date <= end_date:
                if tx.transaction_type == TransactionType.SELL:
                    total += tx.quantity * tx.price_per_unit
        return total

    def _calculate_gross_received(
        self, holding: dict, start_date: datetime, end_date: datetime
    ) -> Decimal:
        """Dividends/interest received during the calendar year"""
        # TODO: Integrate with dividend tracking when implemented
        return Decimal(0)

    def _get_country_info(self, asset: Asset) -> tuple:
        """Get country code and name from asset or currency"""
        country = getattr(asset, 'country', None)
        if country:
            return country, country

        # Default from currency
        currency_country_map = {
            "USD": ("US", "United States"),
            "GBP": ("GB", "United Kingdom"),
            "EUR": ("DE", "Germany"),
            "CAD": ("CA", "Canada"),
            "AUD": ("AU", "Australia"),
            "SGD": ("SG", "Singapore"),
            "JPY": ("JP", "Japan"),
        }
        return currency_country_map.get(asset.currency, ("", ""))

    def _get_entity_nature(self, asset: Asset) -> str:
        """Determine nature of entity for Schedule FA"""
        asset_type = str(asset.asset_type).upper()
        if "STOCK" in asset_type or "ETF" in asset_type:
            return "Shares"
        if "BOND" in asset_type:
            return "Debt Securities"
        if "MUTUAL" in asset_type:
            return "Units"
        return "Other"
