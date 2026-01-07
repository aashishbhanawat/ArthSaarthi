import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict

import pandas as pd
from pyxirr import xirr
from sqlalchemy.orm import Session

from app import crud
from app.services.financial_data_service import FinancialDataService

logger = logging.getLogger(__name__)

class BenchmarkService:
    def __init__(self, db: Session, financial_service: FinancialDataService):
        self.db = db
        self.financial_service = financial_service

    def calculate_benchmark_performance(
        self, portfolio_id: str, benchmark_ticker: str = "^NSEI"
    ) -> Dict:
        """
        Calculates portfolio performance vs hypothetical benchmark performance.
        Returns:
        {
            "portfolio_xirr": float,
            "benchmark_xirr": float,
            "chart_data": [
                {
                    "date": "YYYY-MM-DD",
                    "portfolio_value": 1000,
                    "benchmark_value": 1050,
                    "invested_amount": 1000
                },
                ...
            ]
        }
        """
        # 1. Fetch all portfolio transactions
        transactions = crud.transaction.get_multi_by_portfolio(
            self.db, portfolio_id=portfolio_id
        )
        if not transactions:
            return {
                "portfolio_xirr": 0.0,
                "benchmark_xirr": 0.0,
                "chart_data": []
            }

        # Sort transactions by date
        transactions.sort(key=lambda x: x.transaction_date)
        start_date = transactions[0].transaction_date.date()
        end_date = date.today()

        # 2. Fetch Benchmark History
        index_history = self.financial_service.yfinance_provider.get_index_history(
            benchmark_ticker, start_date, end_date
        )
        if not index_history:
            logger.warning(f"Could not fetch history for benchmark {benchmark_ticker}")
            # Fallback: Just return portfolio XIRR
            # Fallback: Just return portfolio XIRR
            pf_analytics = crud.analytics.get_portfolio_analytics(
                self.db, portfolio_id=portfolio_id
            )
            if pf_analytics:
                if isinstance(pf_analytics, dict):
                    portfolio_xirr = pf_analytics.get("xirr", 0.0)
                else:
                    portfolio_xirr = getattr(pf_analytics, "xirr", 0.0)
            else:
                portfolio_xirr = 0.0

            return {
                "portfolio_xirr": portfolio_xirr,
                "benchmark_xirr": 0.0,
                "chart_data": []
            }

        # 3. Simulate Daily Values
        chart_data = []

        # Benchmark Simulation State
        bench_units = 0.0
        invested_amount = Decimal("0")

        # Cashflows for XIRR
        xirr_cashflows_bench = []

        # Pre-process transactions
        txns_by_date = {}
        for txn in transactions:
            d_str = txn.transaction_date.date().isoformat()
            if d_str not in txns_by_date:
                txns_by_date[d_str] = []
            txns_by_date[d_str].append(txn)

        date_range = pd.date_range(start=start_date, end=end_date)

        for d in date_range:
            d_date = d.date()
            d_str = d_date.isoformat()

            bench_price = self._get_price_for_date(index_history, d_date)

            daily_txns = txns_by_date.get(d_str, [])

            # XIRR Flow for this day (sum of all txns)
            daily_flow_xirr = 0.0

            for txn in daily_txns:
                amount = txn.quantity * txn.price_per_unit
                # Convert enum to string for comparison
                tx_type = str(txn.transaction_type)
                if hasattr(txn.transaction_type, 'value'):
                    tx_type = txn.transaction_type.value

                # For foreign stocks, convert amount to INR using fx_rate
                # This is needed because benchmark (^NSEI) is in INR
                amount_inr = amount
                if txn.details and isinstance(txn.details, dict):
                    fx_rate = txn.details.get("fx_rate")
                    if fx_rate and float(fx_rate) > 0:
                        amount_inr = amount * Decimal(str(fx_rate))

                # Update Invested Amount
                # Inflows: BUY, DEPOSIT, RSU_VEST, ESPP_PURCHASE, BONUS
                if tx_type in [
                    "BUY", "DEPOSIT", "RSU_VEST", "ESPP_PURCHASE", "BONUS"
                ]:
                    invested_amount += amount_inr
                    if bench_price > 0:
                        units_bought = float(amount_inr) / bench_price
                        bench_units += units_bought
                    daily_flow_xirr -= float(amount_inr)  # Outflow

                elif tx_type in ["SELL", "WITHDRAWAL"]:
                    invested_amount -= amount_inr
                    if bench_price > 0:
                        units_sold = float(amount_inr) / bench_price
                        bench_units -= units_sold
                    daily_flow_xirr += float(amount_inr)  # Inflow

            if daily_flow_xirr != 0:
                xirr_cashflows_bench.append((d_date, daily_flow_xirr))

            # Calculate Daily Values
            bench_value = bench_units * bench_price if bench_price > 0 else 0.0

            chart_data.append({
                "date": d_str,
                "benchmark_value": round(bench_value, 2),
                "invested_amount": float(invested_amount)
            })

        # Calculate Benchmark XIRR
        final_bench_value = chart_data[-1]["benchmark_value"]
        xirr_cashflows_bench.append((end_date, final_bench_value))

        logger.debug(
            f"Benchmark XIRR inputs: {len(xirr_cashflows_bench)} cashflows, "
            f"final_value={final_bench_value}"
        )

        try:
            dates = [d for d, v in xirr_cashflows_bench]
            values = [v for d, v in xirr_cashflows_bench]
            benchmark_xirr = xirr(dates, values)
            benchmark_xirr = float(benchmark_xirr) if benchmark_xirr else 0.0
            logger.debug(f"Benchmark XIRR calculated: {benchmark_xirr}")
        except Exception as e:
            logger.warning(f"Failed to calculate benchmark XIRR: {e}")
            benchmark_xirr = 0.0

        # Portfolio XIRR
        pf_analytics = crud.analytics.get_portfolio_analytics(
            self.db, portfolio_id=portfolio_id
        )
        if pf_analytics:
            if isinstance(pf_analytics, dict):
                portfolio_xirr = pf_analytics.get("xirr", 0.0)
            else:
                portfolio_xirr = getattr(pf_analytics, "xirr", 0.0)
        else:
            portfolio_xirr = 0.0

        return {
            "portfolio_xirr": portfolio_xirr,
            "benchmark_xirr": benchmark_xirr,
            "chart_data": chart_data
        }

    def _get_price_for_date(self, history: Dict[str, float], d: date) -> float:
        """Finds price for date, or looks back/forward up to 7 days."""
        d_str = d.isoformat()
        if d_str in history:
            return history[d_str]

        # Look back first (for weekends/holidays mid-range)
        for i in range(1, 8):
            prev_d = d - timedelta(days=i)
            prev_d_str = prev_d.isoformat()
            if prev_d_str in history:
                return history[prev_d_str]

        # Look forward (for dates at the start of the range)
        for i in range(1, 8):
            next_d = d + timedelta(days=i)
            next_d_str = next_d.isoformat()
            if next_d_str in history:
                return history[next_d_str]

        return 0.0
