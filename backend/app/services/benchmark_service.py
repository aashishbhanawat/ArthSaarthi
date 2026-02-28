import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Tuple

import pandas as pd
from pyxirr import xirr
from sqlalchemy.orm import Session

from app import crud
from app.services.financial_data_service import FinancialDataService

logger = logging.getLogger(__name__)

# Transaction types that represent inflows
BUY_TYPES = [
    "BUY", "DEPOSIT", "RSU_VEST",
    "ESPP_PURCHASE", "BONUS",
]

HYBRID_PRESETS = {
    "CRISIL_HYBRID_35_65": {
        "label": "CRISIL Hybrid 35+65 (Aggressive)",
        "components": [
            {"ticker": "^NSEI", "weight": 0.35},
            # Fallback: use risk-free rate for debt
            {"ticker": "^CRSLDX", "weight": 0.65},
        ]
    },
    "BALANCED_50_50": {
        "label": "Balanced 50/50",
        "components": [
            {"ticker": "^NSEI", "weight": 0.50},
            {"ticker": "^CRSLDX", "weight": 0.50},
        ]
    },
}


class BenchmarkService:
    def __init__(
        self, db: Session,
        financial_service: FinancialDataService
    ):
        self.db = db
        self.financial_service = financial_service

    def _calculate_risk_free_values(
        self,
        date_range: pd.DatetimeIndex,
        txns_by_date: Dict,
        start_date: date,
        end_date: date,
        annual_rate: float,
    ) -> Tuple[Dict[str, float], float]:
        """Calculate daily values and XIRR for risk-free growth."""
        daily_values = {}
        daily_rate = (1 + annual_rate / 100) ** (1 / 365) - 1

        current_value = 0.0
        xirr_cashflows = []

        for d in date_range:
            d_date = d.date()
            d_str = d_date.isoformat()

            # Add daily interest to previous balance
            current_value *= (1 + daily_rate)

            # Process cash flows for the day
            daily_txns = txns_by_date.get(d_str, [])
            daily_flow_xirr = 0.0

            for txn in daily_txns:
                amount = float(
                    txn.quantity * txn.price_per_unit
                )
                tx_type = str(txn.transaction_type)
                if hasattr(txn.transaction_type, 'value'):
                    tx_type = txn.transaction_type.value

                # Convert foreign currency if needed
                if txn.details and isinstance(
                    txn.details, dict
                ):
                    fx_rate = txn.details.get("fx_rate")
                    if fx_rate and float(fx_rate) > 0:
                        amount *= float(fx_rate)

                if tx_type in BUY_TYPES:
                    current_value += amount
                    daily_flow_xirr -= amount
                elif tx_type in ["SELL", "WITHDRAWAL"]:
                    current_value -= amount
                    daily_flow_xirr += amount

            if daily_flow_xirr != 0:
                xirr_cashflows.append(
                    (d_date, daily_flow_xirr)
                )

            daily_values[d_str] = current_value

        # Calculate XIRR
        xirr_cashflows.append((end_date, current_value))

        try:
            dates = [d for d, v in xirr_cashflows]
            values = [v for d, v in xirr_cashflows]
            rf_xirr = xirr(dates, values)
            rf_xirr = float(rf_xirr) if rf_xirr else 0.0
        except Exception as e:
            logger.warning(
                f"Failed to calculate risk-free XIRR: {e}"
            )
            rf_xirr = 0.0

        return daily_values, rf_xirr

    def _calculate_category_benchmark(
        self, portfolio_id: str, risk_free_rate: float
    ) -> Dict:
        """Split txns into equity/debt and benchmark."""
        txns = crud.transaction.get_multi_by_portfolio(
            self.db, portfolio_id=portfolio_id
        )
        if not txns:
            return {"equity": None, "debt": None}

        equity_txns = []
        debt_txns = []

        # Normalize: DB stores mixed formats like
        # "Mutual Fund", "MUTUAL_FUND", "STOCK", etc.
        equity_types = [
            "STOCK", "MUTUAL FUND", "ETF", "ESPP", "RSU",
        ]

        assets = crud.asset.get_multi_by_portfolio(
            self.db, portfolio_id=portfolio_id
        )
        asset_map = {a.id: a.asset_type for a in assets}

        for txn in txns:
            a_type = asset_map.get(txn.asset_id, "STOCK")
            if hasattr(a_type, 'value'):
                a_type = a_type.value
            # Normalize to upper with spaces
            a_type_norm = str(a_type).upper().replace(
                "_", " "
            )

            if a_type_norm in equity_types:
                equity_txns.append(txn)
            else:
                debt_txns.append(txn)

        logger.debug(
            f"Category split: {len(equity_txns)} equity, "
            f"{len(debt_txns)} debt from "
            f"{len(txns)} total txns. "
            f"Asset types: {dict(asset_map)}"
        )

        results = {}

        if equity_txns:
            results["equity"] = self._run_simulation(
                equity_txns,
                portfolio_id,
                benchmark_ticker="^NSEI",
                benchmark_mode="single",
                hybrid_preset=None,
                risk_free_rate=risk_free_rate,
            )
            results["equity"]["benchmark_label"] = "Nifty 50"

        if debt_txns:
            results["debt"] = self._run_simulation(
                debt_txns,
                portfolio_id,
                benchmark_ticker="^CRSLDX",
                benchmark_mode="single",
                hybrid_preset=None,
                risk_free_rate=risk_free_rate,
            )
            debt_xirr = results["debt"]["benchmark_xirr"]
            is_rf = debt_xirr == risk_free_rate / 100
            results["debt"]["benchmark_label"] = (
                "Risk-Free (7%)" if is_rf else "Bond Index"
            )

        logger.debug(
            f"Category results keys: {list(results.keys())}"
        )

        return results

    def calculate_benchmark_performance(
        self,
        portfolio_id: str,
        benchmark_ticker: str = "^NSEI",
        benchmark_mode: str = "single",
        hybrid_preset: str = None,
        risk_free_rate: float = 7.0,
    ) -> Dict:
        """
        Calculate portfolio vs hypothetical benchmark.

        Supports single, hybrid, and category modes,
        plus risk-free overlay.
        """
        if benchmark_mode == "category":
            category_data = (
                self._calculate_category_benchmark(
                    portfolio_id, risk_free_rate
                )
            )
            base_result = self._run_simulation(
                None, portfolio_id,
                benchmark_ticker, "single",
                None, risk_free_rate,
            )
            base_result["category_data"] = category_data
            logger.debug(
                f"Category response: "
                f"category_data keys="
                f"{list(category_data.keys())}, "
                f"has equity="
                f"{'equity' in category_data}, "
                f"has debt="
                f"{'debt' in category_data}"
            )
            return base_result

        return self._run_simulation(
            None, portfolio_id,
            benchmark_ticker, benchmark_mode,
            hybrid_preset, risk_free_rate,
        )

    def _run_simulation(
        self,
        transactions: list = None,
        portfolio_id: str = None,
        benchmark_ticker: str = "^NSEI",
        benchmark_mode: str = "single",
        hybrid_preset: str = None,
        risk_free_rate: float = 7.0,
    ) -> Dict:
        # 1. Fetch all portfolio transactions if not provided
        if not transactions:
            transactions = (
                crud.transaction.get_multi_by_portfolio(
                    self.db, portfolio_id=portfolio_id
                )
            )

        if not transactions:
            return {
                "portfolio_xirr": 0.0,
                "benchmark_xirr": 0.0,
                "risk_free_xirr": 0.0,
                "chart_data": [],
            }

        # Sort transactions by date
        transactions.sort(
            key=lambda x: x.transaction_date
        )
        start_date = transactions[0].transaction_date.date()
        end_date = date.today()

        # 2. Fetch Benchmark History(ies)
        yf = self.financial_service.yfinance_provider
        histories = {}
        if (
            benchmark_mode == "hybrid"
            and hybrid_preset in HYBRID_PRESETS
        ):
            preset = HYBRID_PRESETS[hybrid_preset]
            for comp in preset["components"]:
                ticker = comp["ticker"]
                hist = yf.get_index_history(
                    ticker, start_date, end_date
                )
                if hist:
                    histories[ticker] = hist
                else:
                    logger.warning(
                        "Could not fetch history for "
                        f"hybrid component {ticker}"
                    )
        else:
            hist = yf.get_index_history(
                benchmark_ticker, start_date, end_date
            )
            if hist:
                histories[benchmark_ticker] = hist
            else:
                logger.warning(
                    "Could not fetch history for "
                    f"benchmark {benchmark_ticker}"
                )

        # Portfolio XIRR — use cached analytics when we
        # have all txns, otherwise calculate from subset.
        portfolio_xirr = 0.0
        is_full_portfolio = False
        if portfolio_id:
            all_txns = (
                crud.transaction.get_multi_by_portfolio(
                    self.db, portfolio_id=portfolio_id
                )
            )
            is_full_portfolio = (
                len(transactions) == len(all_txns)
            )

        if is_full_portfolio:
            pf_analytics = (
                crud.analytics.get_portfolio_analytics(
                    self.db, portfolio_id=portfolio_id
                )
            )
            if pf_analytics:
                if isinstance(pf_analytics, dict):
                    portfolio_xirr = pf_analytics.get(
                        "xirr", 0.0
                    )
                else:
                    portfolio_xirr = getattr(
                        pf_analytics, "xirr", 0.0
                    )
        else:
            # Calculate XIRR from transaction subset
            portfolio_xirr = self._calc_subset_xirr(
                transactions, end_date
            )

        # 3. Pre-process transactions
        txns_by_date = {}
        for txn in transactions:
            d_str = txn.transaction_date.date().isoformat()
            if d_str not in txns_by_date:
                txns_by_date[d_str] = []
            txns_by_date[d_str].append(txn)

        date_range = pd.date_range(
            start=start_date, end=end_date
        )

        # 4. Calculate Risk-Free Values
        rf_vals, risk_free_xirr = (
            self._calculate_risk_free_values(
                date_range, txns_by_date,
                start_date, end_date, risk_free_rate,
            )
        )

        # Basic fallback check
        if benchmark_mode == "single" and not histories:
            return {
                "portfolio_xirr": portfolio_xirr,
                "benchmark_xirr": 0.0,
                "risk_free_xirr": risk_free_xirr,
                "chart_data": [
                    {
                        "date": d.date().isoformat(),
                        "benchmark_value": 0.0,
                        "invested_amount": 0.0,
                        "risk_free_value": rf_vals.get(
                            d.date().isoformat(), 0.0
                        ),
                    }
                    for d in date_range
                ],
            }

        # 5. Simulate Daily Values
        chart_data = self._simulate_daily(
            date_range, txns_by_date, histories,
            components=(
                HYBRID_PRESETS[hybrid_preset]["components"]
                if (
                    benchmark_mode == "hybrid"
                    and hybrid_preset in HYBRID_PRESETS
                )
                else [
                    {"ticker": benchmark_ticker,
                     "weight": 1.0}
                ]
            ),
            risk_free_rate=risk_free_rate,
            rf_daily_values=rf_vals,
        )

        # Calculate Benchmark XIRR
        bench_xirr = self._calc_bench_xirr(
            chart_data, end_date, date_range,
            txns_by_date, histories,
        )

        return {
            "portfolio_xirr": portfolio_xirr,
            "benchmark_xirr": bench_xirr,
            "risk_free_xirr": risk_free_xirr,
            "chart_data": chart_data,
        }

    def _calc_subset_xirr(
        self, transactions, end_date
    ) -> float:
        """Calculate XIRR from a transaction subset."""
        try:
            pf_cashflows = []
            current_invested = 0.0
            for txn in transactions:
                amount = float(
                    txn.quantity * txn.price_per_unit
                )
                tx_type = str(txn.transaction_type)
                if hasattr(
                    txn.transaction_type, 'value'
                ):
                    tx_type = txn.transaction_type.value

                if (
                    txn.details
                    and isinstance(txn.details, dict)
                ):
                    fx = txn.details.get("fx_rate")
                    if fx and float(fx) > 0:
                        amount *= float(fx)

                if tx_type in BUY_TYPES:
                    pf_cashflows.append(
                        (txn.transaction_date.date(),
                         -amount)
                    )
                    current_invested += amount
                elif tx_type in ["SELL", "WITHDRAWAL"]:
                    pf_cashflows.append(
                        (txn.transaction_date.date(),
                         amount)
                    )
                    current_invested -= amount

            if current_invested > 0 and pf_cashflows:
                pf_cashflows.append(
                    (end_date, current_invested)
                )
                pf_dates = [d for d, v in pf_cashflows]
                pf_values = [v for d, v in pf_cashflows]
                result = xirr(pf_dates, pf_values)
                return float(result) if result else 0.0
        except Exception as e:
            logger.warning(
                f"Failed to calculate subset XIRR: {e}"
            )
        return 0.0

    def _simulate_daily(
        self,
        date_range,
        txns_by_date,
        histories,
        components,
        risk_free_rate,
        rf_daily_values,
    ) -> list:
        """Simulate daily benchmark values."""
        chart_data = []
        bench_units = {
            comp["ticker"]: 0.0 for comp in components
        }
        invested_amount = Decimal("0")
        daily_rf = (
            (1 + risk_free_rate / 100) ** (1 / 365) - 1
        )

        for d in date_range:
            d_date = d.date()
            d_str = d_date.isoformat()

            daily_prices = {}
            for comp in components:
                ticker = comp["ticker"]
                if ticker in histories:
                    daily_prices[ticker] = (
                        self._get_price_for_date(
                            histories[ticker], d_date
                        )
                    )
                else:
                    daily_prices[ticker] = 1.0

            daily_txns = txns_by_date.get(d_str, [])

            for txn in daily_txns:
                amount = float(
                    txn.quantity * txn.price_per_unit
                )
                tx_type = str(txn.transaction_type)
                if hasattr(
                    txn.transaction_type, 'value'
                ):
                    tx_type = txn.transaction_type.value

                amount_inr = amount
                if (
                    txn.details
                    and isinstance(txn.details, dict)
                ):
                    fx = txn.details.get("fx_rate")
                    if fx and float(fx) > 0:
                        amount_inr = amount * float(fx)

                if tx_type in BUY_TYPES:
                    invested_amount += Decimal(
                        str(amount_inr)
                    )
                    for comp in components:
                        ticker = comp["ticker"]
                        weight = comp["weight"]
                        comp_amt = amount_inr * weight
                        price = daily_prices[ticker]
                        if price > 0:
                            if ticker not in histories:
                                bench_units[ticker] += (
                                    comp_amt
                                )
                            else:
                                bench_units[ticker] += (
                                    comp_amt / price
                                )

                elif tx_type in ["SELL", "WITHDRAWAL"]:
                    invested_amount -= Decimal(
                        str(amount_inr)
                    )
                    total_val = 0
                    for c in components:
                        t = c["ticker"]
                        p = daily_prices[t]
                        if t not in histories:
                            total_val += bench_units[t]
                        else:
                            total_val += (
                                bench_units[t] * p
                            )

                    if total_val > 0:
                        ratio = amount_inr / total_val
                        for comp in components:
                            ticker = comp["ticker"]
                            if ticker not in histories:
                                bench_units[ticker] -= (
                                    bench_units[ticker]
                                    * ratio
                                )
                            else:
                                bench_units[ticker] -= (
                                    bench_units[ticker]
                                    * ratio
                                )

            bench_value = 0.0
            for comp in components:
                ticker = comp["ticker"]
                price = daily_prices[ticker]
                if ticker not in histories:
                    bench_units[ticker] *= (1 + daily_rf)
                    bench_value += bench_units[ticker]
                else:
                    bench_value += (
                        bench_units[ticker] * price
                        if price > 0 else 0.0
                    )

            rf_val = rf_daily_values.get(d_str, 0.0)
            chart_data.append({
                "date": d_str,
                "benchmark_value": round(
                    bench_value, 2
                ),
                "invested_amount": float(
                    invested_amount
                ),
                "risk_free_value": round(rf_val, 2),
            })

        return chart_data

    def _calc_bench_xirr(
        self, chart_data, end_date,
        date_range, txns_by_date, histories,
    ) -> float:
        """Calculate benchmark XIRR from chart data."""
        xirr_cashflows = []
        for d in date_range:
            d_str = d.date().isoformat()
            daily_txns = txns_by_date.get(d_str, [])
            daily_flow = 0.0
            for txn in daily_txns:
                amount = float(
                    txn.quantity * txn.price_per_unit
                )
                tx_type = str(txn.transaction_type)
                if hasattr(
                    txn.transaction_type, 'value'
                ):
                    tx_type = txn.transaction_type.value

                amount_inr = amount
                if (
                    txn.details
                    and isinstance(txn.details, dict)
                ):
                    fx = txn.details.get("fx_rate")
                    if fx and float(fx) > 0:
                        amount_inr = amount * float(fx)

                if tx_type in BUY_TYPES:
                    daily_flow -= amount_inr
                elif tx_type in ["SELL", "WITHDRAWAL"]:
                    daily_flow += amount_inr

            if daily_flow != 0:
                xirr_cashflows.append(
                    (d.date(), daily_flow)
                )

        final_val = chart_data[-1]["benchmark_value"]
        xirr_cashflows.append((end_date, final_val))

        logger.debug(
            f"Benchmark XIRR inputs: "
            f"{len(xirr_cashflows)} cashflows, "
            f"final_value={final_val}"
        )

        try:
            dates = [d for d, v in xirr_cashflows]
            values = [v for d, v in xirr_cashflows]
            bench_xirr = xirr(dates, values)
            bench_xirr = (
                float(bench_xirr) if bench_xirr else 0.0
            )
            logger.debug(
                f"Benchmark XIRR calculated: {bench_xirr}"
            )
            return bench_xirr
        except Exception as e:
            logger.warning(
                f"Failed to calculate benchmark XIRR: {e}"
            )
            return 0.0

    def _get_price_for_date(
        self, history: Dict[str, float], d: date
    ) -> float:
        """Find price for date, looking ±7 days."""
        d_str = d.isoformat()
        if d_str in history:
            return history[d_str]

        # Look back first (weekends/holidays)
        for i in range(1, 8):
            prev_d = d - timedelta(days=i)
            prev_str = prev_d.isoformat()
            if prev_str in history:
                return history[prev_str]

        # Look forward (start of range)
        for i in range(1, 8):
            next_d = d + timedelta(days=i)
            next_str = next_d.isoformat()
            if next_str in history:
                return history[next_str]

        return 0.0
