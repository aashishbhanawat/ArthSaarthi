import logging
import time
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, Tuple

import pandas as pd
from dateutil.relativedelta import relativedelta
from pyxirr import xirr
from sqlalchemy.orm import Session

from app import crud
from app.crud.crud_holding import (
    _calculate_fd_current_value,
    _calculate_rd_value_at_date,
)
from app.services.financial_data_service import FinancialDataService

logger = logging.getLogger(__name__)

# Transaction types that represent inflows
BUY_TYPES = [
    "BUY", "DEPOSIT", "RSU_VEST",
    "ESPP_PURCHASE", "CONTRIBUTION",
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

    def _generate_synthetic_transactions(
        self, portfolio_id: str
    ) -> list:
        """Generate synthetic transactions for FDs and RDs."""
        synthetic_txns = []

        # 1. Fetch FDs
        fds = crud.fixed_deposit.get_multi_by_portfolio(
            self.db, portfolio_id=portfolio_id
        )
        for fd in fds:
            # Initial Investment (BUY)
            synthetic_txns.append(
                self._create_mock_txn(
                    fd.start_date, fd.principal_amount, "BUY"
                )
            )

            # Interest Payouts
            if (fd.interest_payout or "").upper() == "PAYOUT":
                interval_map = {
                    "MONTHLY": relativedelta(months=1),
                    "QUARTERLY": relativedelta(months=3),
                    "HALF_YEARLY": relativedelta(months=6),
                    "SEMI-ANNUALLY": relativedelta(months=6),
                    "ANNUALLY": relativedelta(years=1),
                }
                interval = interval_map.get(
                    (fd.compounding_frequency or "").upper()
                )
                if interval:
                    # Simplified payout calculation
                    if interval.months:
                        divisor = Decimal(12) / Decimal(interval.months)
                    else:
                        divisor = Decimal(1)

                    period_payout = (
                        fd.principal_amount *
                        (Decimal(str(fd.interest_rate)) / 100) /
                        divisor
                    )
                    curr_date = fd.start_date + interval
                    while curr_date <= min(fd.maturity_date, date.today()):
                        synthetic_txns.append(
                            self._create_mock_txn(
                                curr_date, period_payout, "DIVIDEND"
                            )
                        )
                        curr_date += interval

            # Maturity (SELL)
            if fd.maturity_date <= date.today():
                maturity_value = _calculate_fd_current_value(
                    principal=fd.principal_amount,
                    interest_rate=fd.interest_rate,
                    start_date=fd.start_date,
                    end_date=fd.maturity_date,
                    compounding_frequency=fd.compounding_frequency,
                    interest_payout=fd.interest_payout
                )
                synthetic_txns.append(
                    self._create_mock_txn(
                        fd.maturity_date, maturity_value, "SELL"
                    )
                )

        # 2. Fetch RDs
        rds = crud.recurring_deposit.get_multi_by_portfolio(
            self.db, portfolio_id=portfolio_id
        )
        for rd in rds:
            # Monthly Deposits (BUY)
            curr_date = rd.start_date
            maturity_date = rd.start_date + relativedelta(months=rd.tenure_months)
            for _ in range(rd.tenure_months):
                if curr_date > date.today():
                    break
                synthetic_txns.append(
                    self._create_mock_txn(
                        curr_date, rd.monthly_installment, "BUY"
                    )
                )
                curr_date += relativedelta(months=1)

            # Maturity (SELL)
            if maturity_date <= date.today():
                maturity_value = _calculate_rd_value_at_date(
                    monthly_installment=rd.monthly_installment,
                    interest_rate=rd.interest_rate,
                    start_date=rd.start_date,
                    tenure_months=rd.tenure_months,
                    calculation_date=maturity_date
                )
                synthetic_txns.append(
                    self._create_mock_txn(
                        maturity_date, maturity_value, "SELL"
                    )
                )

        return synthetic_txns

    def _create_mock_txn(
        self, t_date: date, amount: Decimal, t_type: str
    ) -> Any:
        """Create a mock transaction object for simulation."""
        import uuid
        from datetime import datetime

        from app.schemas.asset import Asset
        from app.schemas.transaction import Transaction

        mock_id = uuid.uuid4()
        return Transaction(
            id=mock_id,
            portfolio_id=mock_id,
            transaction_date=datetime.combine(t_date, datetime.min.time()),
            transaction_type=t_type,
            quantity=Decimal("1"),
            price_per_unit=amount,
            asset=Asset(
                id=mock_id,
                ticker_symbol="FD-RD-MOCK",
                name="FD/RD Synthetic",
                asset_type="DEBT"
            ),
            details={}
        )

    def _get_transaction_amount(self, txn: Any, tx_type: str) -> float:
        """Helper to compute txn amount, handling special cases like RSU_VEST."""
        if tx_type == "RSU_VEST" and txn.details:
            fmv = Decimal(str(txn.details.get("fmv", 0)))
            return float(txn.quantity * fmv)
        return float(txn.quantity * txn.price_per_unit)

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
                tx_type = str(txn.transaction_type)
                if hasattr(txn.transaction_type, 'value'):
                    tx_type = txn.transaction_type.value

                amount = self._get_transaction_amount(txn, tx_type)

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
                elif tx_type in ["SELL", "WITHDRAWAL", "DIVIDEND", "COUPON"]:
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

        equity_txns = []
        debt_txns = []

        # Normalize: DB stores mixed formats like
        # "Mutual Fund", "MUTUAL_FUND", "STOCK", etc.
        equity_types = [
            "STOCK", "MUTUAL FUND", "ETF", "ESPP", "RSU",
        ]

        if txns:
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
            f"{len(txns)} total txns."
        )

        # Get current market values per category
        equity_value = 0.0
        debt_value = 0.0
        has_fd_or_rd = False
        try:
            holdings_data = (
                crud.holding
                .get_portfolio_holdings_and_summary(
                    self.db, portfolio_id=portfolio_id
                )
            )
            for h in holdings_data.holdings:
                h_type = str(
                    getattr(h, 'asset_type', '')
                ).upper().replace("_", " ")
                cv = float(
                    getattr(h, 'current_value', 0) or 0
                )
                if h_type in equity_types:
                    equity_value += cv
                else:
                    debt_value += cv
                    # Track if we have FD/RD holdings
                    if h_type in [
                        "FIXED DEPOSIT", "RECURRING DEPOSIT"
                    ]:
                        has_fd_or_rd = True
            logger.debug(
                f"Category values: equity={equity_value}, "
                f"debt={debt_value}, has_fd_or_rd={has_fd_or_rd}"
            )
        except Exception as e:
            logger.warning(
                f"Could not get holdings for "
                f"category values: {e}"
            )

        # If there are no transactions AND no FD/RD holdings,
        # there is truly nothing to benchmark.
        if not txns and not has_fd_or_rd:
            return {"equity": None, "debt": None}

        results = {}

        if equity_txns:
            results["equity"] = self._run_simulation(
                equity_txns,
                portfolio_id,
                benchmark_ticker="^NSEI",
                benchmark_mode="single",
                hybrid_preset=None,
                risk_free_rate=risk_free_rate,
                subset_current_value=equity_value,
            )
            results["equity"]["benchmark_label"] = (
                "Nifty 50"
            )

        if debt_txns:
            results["debt"] = self._run_simulation(
                debt_txns,
                portfolio_id,
                benchmark_ticker="^CRSLDX",
                benchmark_mode="single",
                hybrid_preset=None,
                risk_free_rate=risk_free_rate,
                subset_current_value=debt_value,
            )
            debt_xirr = results["debt"]["benchmark_xirr"]

            # Since _simulate_daily uses risk_free_rate if index is absent,
            # bench_xirr will closely match it
            # We use a tolerance because floats might not exactly match
            is_rf = abs(debt_xirr - (risk_free_rate / 100)) < 0.001
            results["debt"]["benchmark_label"] = (
                f"Risk-Free ({risk_free_rate:.0f}%)" if is_rf
                else "Bond Index"
            )
        elif has_fd_or_rd and debt_value > 0:
            # FDs/RDs don't have Transaction entries. We generate synthetic
            # transactions and run a risk-free simulation for the benchmark chart.
            synthetic_txns = self._generate_synthetic_transactions(portfolio_id)

            pf_analytics = crud.analytics.get_portfolio_analytics(
                self.db, portfolio_id=portfolio_id
            )
            portfolio_xirr = 0.0
            if pf_analytics:
                if isinstance(pf_analytics, dict):
                    portfolio_xirr = pf_analytics.get("xirr", 0.0)
                else:
                    portfolio_xirr = getattr(pf_analytics, "xirr", 0.0)

            if not synthetic_txns:
                # Still return basic info if there are no synthetic txns for some reason
                # but we know there's debt value.
                results["debt"] = {
                    "portfolio_xirr": portfolio_xirr,
                    "benchmark_xirr": risk_free_rate / 100,
                    "benchmark_label": f"Risk-Free ({risk_free_rate:.0f}%)",
                    "risk_free_xirr": risk_free_rate / 100,
                    "days_duration": 0,
                    "chart_data": [],
                }
                return results

            synthetic_txns.sort(key=lambda x: x.transaction_date)
            start_date = synthetic_txns[0].transaction_date.date()
            end_date = date.today()

            if start_date > end_date: # Handle case where FD is in the future
                results["debt"] = {
                    "portfolio_xirr": portfolio_xirr,
                    "benchmark_xirr": 0.0,
                    "benchmark_label": f"Risk-Free ({risk_free_rate:.0f}%)",
                    "risk_free_xirr": 0.0,
                    "days_duration": 0,
                    "chart_data": [],
                }
                return results

            date_range = pd.date_range(start=start_date, end=end_date)

            txns_by_date = {}
            for txn in synthetic_txns:
                d_str = txn.transaction_date.date().isoformat()
                if d_str not in txns_by_date:
                    txns_by_date[d_str] = []
                txns_by_date[d_str].append(txn)

            rf_vals, risk_free_xirr = self._calculate_risk_free_values(
                date_range, txns_by_date, start_date, end_date, risk_free_rate
            )

            chart_data = self._simulate_daily(
                date_range,
                txns_by_date,
                histories={},
                components=[{"ticker": "RISK_FREE", "weight": 1.0}],
                risk_free_rate=risk_free_rate,
                rf_daily_values=rf_vals,
            )

            bench_xirr = self._calc_bench_xirr(
                chart_data, end_date, date_range, txns_by_date, {}
            )

            results["debt"] = {
                "portfolio_xirr": portfolio_xirr,
                "benchmark_xirr": bench_xirr,
                "benchmark_label": f"Risk-Free ({risk_free_rate:.0f}%)",
                "risk_free_xirr": risk_free_xirr,
                "days_duration": (end_date - start_date).days,
                "chart_data": chart_data,
            }

        logger.debug(
            f"Category results keys: "
            f"{list(results.keys())}"
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
            start_time = time.time()
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

            # For FD/RD-only portfolios, _run_simulation
            # returns portfolio_xirr=0 because there are no
            # transactions. Override with the real analytics.
            if (
                base_result.get("portfolio_xirr", 0) == 0
                and portfolio_id
            ):
                pf_analytics = (
                    crud.analytics.get_portfolio_analytics(
                        self.db, portfolio_id=portfolio_id
                    )
                )
                if pf_analytics:
                    if isinstance(pf_analytics, dict):
                        base_result["portfolio_xirr"] = (
                            pf_analytics.get("xirr", 0.0)
                        )
                    else:
                        base_result["portfolio_xirr"] = (
                            getattr(pf_analytics, "xirr", 0.0)
                        )

                # Add duration for category base results (they are summarized from
                # full data)
                # We can't easily get 'start_date' here without transactions,
                # but these are placeholders mostly.
                if "equity" in category_data:
                    category_data["equity"]["days_duration"] = 0
                if "debt" in category_data:
                    category_data["debt"]["days_duration"] = 0

            logger.debug(
                f"Category response: "
                f"category_data keys="
                f"{list(category_data.keys())}, "
                f"has equity="
                f"{'equity' in category_data}, "
                f"has debt="
                f"{'debt' in category_data}"
            )
            logger.info(
                "Benchmark calculation (category) for portfolio %s "
                "took %.4f seconds.",
                portfolio_id, time.time() - start_time,
            )
            return base_result

        start_time = time.time()
        result = self._run_simulation(
            None, portfolio_id,
            benchmark_ticker, benchmark_mode,
            hybrid_preset, risk_free_rate,
        )
        logger.info(
            "Benchmark calculation (%s) for portfolio %s "
            "took %.4f seconds.",
            benchmark_mode, portfolio_id, time.time() - start_time,
        )
        return result

    def _run_simulation(
        self,
        transactions: list = None,
        portfolio_id: str = None,
        benchmark_ticker: str = "^NSEI",
        benchmark_mode: str = "single",
        hybrid_preset: str = None,
        risk_free_rate: float = 7.0,
        subset_current_value: float = None,
    ) -> Dict:
        # 1. Fetch all portfolio transactions if not provided
        if not transactions:
            transactions = (
                crud.transaction.get_multi_by_portfolio(
                    self.db, portfolio_id=portfolio_id
                )
            )

        # Include synthetic transactions for FDs and RDs if it's a full portfolio
        synthetic_txns = []
        if portfolio_id:
            # Check if we should add FDs/RDs (always for full portfolio benchmark)
            # or if we have no other transactions
            if not transactions or (not subset_current_value):
                synthetic_txns = self._generate_synthetic_transactions(
                    portfolio_id
                )
                transactions = transactions + synthetic_txns

        if not transactions:
            return {
                "portfolio_xirr": 0.0,
                "benchmark_xirr": 0.0,
                "risk_free_xirr": 0.0,
                "days_duration": 0,
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
            all_real_txns = (
                crud.transaction.get_multi_by_portfolio(
                    self.db, portfolio_id=portfolio_id
                )
            )
            # If we used synthetic txns, we are by definition
            # doing a "full" portfolio benchmarking of what we have.
            is_full_portfolio = (
                len(transactions) == (len(all_real_txns) + len(synthetic_txns))
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
                transactions, end_date,
                subset_current_value,
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
            "days_duration": (end_date - start_date).days,
            "chart_data": chart_data,
        }

    def _calc_subset_xirr(
        self, transactions, end_date,
        current_value: float = None,
    ) -> float:
        """Calculate XIRR from a transaction subset."""
        try:
            pf_cashflows = []
            current_invested = 0.0
            for txn in transactions:
                tx_type = str(txn.transaction_type)
                if hasattr(
                    txn.transaction_type, 'value'
                ):
                    tx_type = txn.transaction_type.value

                amount = self._get_transaction_amount(txn, tx_type)

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
                elif tx_type in ["SELL", "WITHDRAWAL", "DIVIDEND", "COUPON"]:
                    pf_cashflows.append(
                        (txn.transaction_date.date(),
                         amount)
                    )
                    if tx_type not in ["DIVIDEND", "COUPON"]:
                        current_invested -= amount

            # Use actual current value if provided,
            # otherwise fall back to net invested
            terminal_value = (
                current_value
                if current_value and current_value > 0
                else current_invested
            )
            if terminal_value > 0 and pf_cashflows:
                pf_cashflows.append(
                    (end_date, terminal_value)
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

        # Track lots by asset_id to correctly withdraw benchmark units on SELL
        lots_by_asset = {}

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
                tx_type = str(txn.transaction_type)
                if hasattr(
                    txn.transaction_type, 'value'
                ):
                    tx_type = txn.transaction_type.value

                amount = self._get_transaction_amount(txn, tx_type)

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

                    lot_units = {}
                    for comp in components:
                        ticker = comp["ticker"]
                        weight = comp["weight"]
                        comp_amt = amount_inr * weight
                        price = daily_prices[ticker]

                        added_units = 0.0
                        if price > 0:
                            if ticker not in histories:
                                added_units = comp_amt
                                bench_units[ticker] += added_units
                            else:
                                added_units = comp_amt / price
                                bench_units[ticker] += added_units

                        lot_units[ticker] = added_units

                    # Save the lot for FIFO removal
                    asset_id = (
                        str(txn.asset_id)
                        if hasattr(txn, "asset_id") and txn.asset_id
                        else "unknown"
                    )
                    if asset_id not in lots_by_asset:
                        lots_by_asset[asset_id] = []
                    lots_by_asset[asset_id].append({
                        'quantity': float(txn.quantity),
                        'units': lot_units
                    })

                elif tx_type in ["SELL", "WITHDRAWAL", "DIVIDEND", "COUPON"]:
                    fallback_to_ratio = False

                    if tx_type not in ["DIVIDEND", "COUPON"]:
                        invested_amount -= Decimal(str(amount_inr))
                        if invested_amount < 0:
                            invested_amount = Decimal("0")

                        # Use FIFO lot matching for SELL/WITHDRAWAL to safely
                        # remove units
                        asset_id = (
                            str(txn.asset_id)
                            if hasattr(txn, "asset_id") and txn.asset_id
                            else "unknown"
                        )
                        sell_qty = float(txn.quantity)
                        lots = lots_by_asset.get(asset_id, [])
                        units_to_remove = {c["ticker"]: 0.0 for c in components}

                        while sell_qty > 0 and lots:
                            lot = lots[0]
                            if lot['quantity'] <= sell_qty:
                                sell_qty -= lot['quantity']
                                for ticker, u in lot['units'].items():
                                    units_to_remove[ticker] += u
                                lots.pop(0)
                            else:
                                ratio = sell_qty / lot['quantity']
                                lot['quantity'] -= sell_qty
                                for ticker, u in lot['units'].items():
                                    removed_u = u * ratio
                                    units_to_remove[ticker] += removed_u
                                    lot['units'][ticker] -= removed_u
                                sell_qty = 0

                        # Apply precise removal
                        for ticker, u in units_to_remove.items():
                            bench_units[ticker] -= u
                            if bench_units[ticker] < 1e-9:
                                bench_units[ticker] = 0.0

                        if sum(units_to_remove.values()) == 0:
                            fallback_to_ratio = True
                    else:
                        # For dividends/coupons, simply use ratio logic
                        fallback_to_ratio = True

                    if fallback_to_ratio:
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
                                if bench_units[ticker] < 1e-9:
                                    bench_units[ticker] = 0.0

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
                tx_type = str(txn.transaction_type)
                if hasattr(
                    txn.transaction_type, 'value'
                ):
                    tx_type = txn.transaction_type.value

                amount = self._get_transaction_amount(txn, tx_type)

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
                elif tx_type in ["SELL", "WITHDRAWAL", "DIVIDEND", "COUPON"]:
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
