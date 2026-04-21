import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction
from app.schemas.dividends import DividendEntry, DividendSummary
from app.schemas.enums import TransactionType
from app.services.financial_data_service import financial_data_service

logger = logging.getLogger(__name__)

class DividendService:
    def __init__(self, db: Session):
        self.db = db
        # Cache TTBR rates internally during a req to avoid repeated DB/API calls
        self._ttbr_cache: Dict[Tuple[str, date], Optional[Decimal]] = {}

    def get_ttbr_date(self, dividend_date: date) -> date:
        """
        Rule 115: TTBR of SBI on the last day of the month immediately preceding
        the month in which the dividend is declared, distributed or paid.
        """
        # First day of the dividend month
        first_day_of_month = dividend_date.replace(day=1)
        # Last day of the previous month
        last_day_of_prev_month = first_day_of_month - timedelta(days=1)
        return last_day_of_prev_month

    def get_advance_tax_period(self, txn_date: date, fy_start_year: int) -> str:
        """
        Groups the transaction date into the standard Advance Tax buckets:
        - Upto 15/6
        - 16/6 - 15/9
        - 16/9 - 15/12
        - 16/12 - 15/3
        - 16/3 - 31/3
        """
        # Quarter end cutoffs
        q1_cutoff = date(fy_start_year, 6, 15)
        q2_cutoff = date(fy_start_year, 9, 15)
        q3_cutoff = date(fy_start_year, 12, 15)
        q4_cutoff = date(fy_start_year + 1, 3, 15)

        if txn_date <= q1_cutoff:
            return "Upto 15/6"
        elif txn_date <= q2_cutoff:
            return "16/6 - 15/9"
        elif txn_date <= q3_cutoff:
            return "16/9 - 15/12"
        elif txn_date <= q4_cutoff:
            return "16/12 - 15/3"
        else:
            return "16/3 - 31/3"

    def get_proxy_ttbr_rate(self, currency: str, ttbr_date: date) -> Optional[Decimal]:
        """
        Fetch proxy TTBR rate (using yfinance via financial_data_service).
        Caches it locally in this instance for performance.
        """
        if currency.upper() == "INR":
            return Decimal("1.0")

        cache_key = (currency, ttbr_date)
        if cache_key in self._ttbr_cache:
            return self._ttbr_cache[cache_key]

        # We fetch rate for (currency) to INR
        rate = financial_data_service.get_exchange_rate(
            currency.upper(), "INR", ttbr_date
        )
        self._ttbr_cache[cache_key] = rate
        return rate

    def get_dividend_report(
        self,
        fy_year: str,
        user_id: str,
        portfolio_id: Optional[str] = None,
    ) -> DividendSummary:
        """
        Generate a dividend report for a specific financial year.
        If portfolio_id is provided, limit to that portfolio.
        """
        # Parse FY dates (fy_year format: "2025-26")
        start_year = int(fy_year.split("-")[0])
        start_date = date(start_year, 4, 1)
        end_date = date(start_year + 1, 3, 31)

        # Base query for DIVIDEND transactions
        query = (
            self.db.query(Transaction)
            .join(Asset, Transaction.asset_id == Asset.id)
            .join(Portfolio, Transaction.portfolio_id == Portfolio.id)
            .filter(
                Transaction.transaction_type == TransactionType.DIVIDEND,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
        )

        if portfolio_id:
            query = query.filter(Transaction.portfolio_id == portfolio_id)
        if user_id:
            query = query.filter(Transaction.user_id == user_id)

        # Sort by date
        transactions = query.order_by(Transaction.transaction_date.asc()).all()

        entries = []
        total_amount_inr = Decimal("0")

        # Initialize bucket totals
        bucket_totals = {
            "Upto 15/6": Decimal("0"),
            "16/6 - 15/9": Decimal("0"),
            "16/9 - 15/12": Decimal("0"),
            "16/12 - 15/3": Decimal("0"),
            "16/3 - 31/3": Decimal("0")
        }

        for txn in transactions:
            asset = txn.asset

            # For dividends, the quantity field and price_per_unit dictate the
            # amount received. (UI often treats quantity as shares held and price
            # as dividend per share, or quantity as dividend amount and price
            # as 1 for cash funds)
            amount_native = txn.quantity * txn.price_per_unit

            currency = asset.currency or "INR"

            entry_data = {
                "transaction_id": str(txn.id),
                "asset_name": asset.name,
                "asset_ticker": asset.ticker_symbol,
                "date": (
                    txn.transaction_date.date()
                    if isinstance(txn.transaction_date, datetime)
                    else txn.transaction_date
                ),
                # The quantity of shares held (sometimes dividend quantity is the
                # amount, UI handles this but let's just pass raw qty)
                "quantity": txn.quantity,
                "amount_native": amount_native,
                "currency": currency,
            }

            if currency.upper() != "INR":
                ttbr_date = self.get_ttbr_date(entry_data["date"])
                ttbr_rate = self.get_proxy_ttbr_rate(currency, ttbr_date)

                entry_data["ttbr_date"] = ttbr_date
                entry_data["ttbr_rate"] = ttbr_rate

                if ttbr_rate:
                    amount_inr = amount_native * ttbr_rate
                else:
                    logger.warning(
                        f"Could not fetch TTBR proxy rate for {currency} on {ttbr_date}"
                    )
                    amount_inr = Decimal("0") # Or leave it as distinct error state
            else:
                amount_inr = amount_native

            # Determine the tax period bucket
            period = self.get_advance_tax_period(entry_data["date"], start_year)

            entry_data["amount_inr"] = amount_inr
            entry_data["period"] = period

            total_amount_inr += amount_inr
            bucket_totals[period] += amount_inr

            entries.append(DividendEntry(**entry_data))

        return DividendSummary(
            fy_year=fy_year,
            entries=entries,
            total_amount_inr=total_amount_inr,
            bucket_totals=bucket_totals
        )
