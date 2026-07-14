from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.benchmark_service import BenchmarkService
from app.services.financial_data_service import FinancialDataService


@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def mock_financial_service():
    return MagicMock(spec=FinancialDataService)

@pytest.fixture
def benchmark_service(mock_db, mock_financial_service):
    return BenchmarkService(mock_db, mock_financial_service)

def test_calculate_benchmark_performance_empty(benchmark_service, mock_db):
    # Mock crud.transaction.get_multi_by_portfolio to return empty list
    with patch("app.crud.transaction.get_multi_by_portfolio", return_value=[]):
        result = benchmark_service.calculate_benchmark_performance("pf_id")
        assert result["portfolio_xirr"] == 0.0
        assert result["benchmark_xirr"] == 0.0
        assert result["chart_data"] == []

def test_calculate_benchmark_performance_success(
    benchmark_service, mock_db, mock_financial_service
):
    # Mock Transactions
    txn1 = MagicMock()
    txn1.transaction_date = datetime(2023, 1, 1)
    txn1.transaction_type = "BUY"
    txn1.quantity = Decimal("100")
    txn1.price_per_unit = Decimal("100")

    txn2 = MagicMock()
    txn2.transaction_date = datetime(2023, 6, 1)
    txn2.transaction_type = "BUY"
    txn2.quantity = Decimal("50")
    txn2.price_per_unit = Decimal("100")

    # Setup mock attributes
    mock_financial_service.yfinance_provider = MagicMock()

    with patch(
        "app.crud.transaction.get_multi_by_portfolio", return_value=[txn1, txn2]
    ):
        # Mock Index History
        # index 100 on Jan 1, 110 on Jun 1, 120 Today
        start_date = date(2023, 1, 1)
        today = date.today()

        index_history = {
            start_date.isoformat(): 100.0,
            date(2023, 6, 1).isoformat(): 110.0,
            today.isoformat(): 120.0,
        }
        mock_financial_service.yfinance_provider.get_index_history.return_value = (
            index_history
        )

        # Mock Portfolio Analytics
        mock_pf_analytics = MagicMock()
        mock_pf_analytics.xirr = 10.5
        with patch(
            "app.crud.analytics.get_portfolio_analytics", return_value=mock_pf_analytics
        ):

            result = benchmark_service.calculate_benchmark_performance("pf_id")

            assert result["portfolio_xirr"] == 10.5
            assert len(result["chart_data"]) > 0

            # Verify calculation logic
            # Buy 100 units at 100 = 10000
            # Buy 45.45 units at 110 = 5000
            # Total units = 145.45
            # Final Value = 145.45 * 120 = 17454
            # Invested = 15000
            # Check final data point
            last_point = result["chart_data"][-1]
            assert last_point["invested_amount"] == 15000.0
            assert last_point["benchmark_value"] > 16000.0 # 17454 > 16000


def test_calculate_benchmark_performance_cached_dict(
    benchmark_service, mock_db, mock_financial_service
):
    # Test handling of cached analytics returned as dict
    txn1 = MagicMock()
    txn1.transaction_date = datetime(2023, 1, 1)
    txn1.transaction_type = "BUY"
    txn1.quantity = Decimal("100")
    txn1.price_per_unit = Decimal("100")
    txn1.asset_id = "asset1"

    # Setup mock attributes
    mock_financial_service.yfinance_provider = MagicMock()

    with patch("app.crud.transaction.get_multi_by_portfolio", return_value=[txn1]):
        mock_financial_service.yfinance_provider.get_index_history.return_value = {
            date(2023, 1, 1).isoformat(): 100.0,
            date.today().isoformat(): 120.0,
        }

        # Mock returns DICT instead of object
        pf_analytics_dict = {"xirr": 12.5}
        with patch(
            "app.crud.analytics.get_portfolio_analytics", return_value=pf_analytics_dict
        ):
            result = benchmark_service.calculate_benchmark_performance("pf_id")
            assert result["portfolio_xirr"] == 12.5

def test_risk_free_rate_calculation(benchmark_service, mock_db, mock_financial_service):
    mock_financial_service.yfinance_provider = MagicMock()
    txn1 = MagicMock()
    txn1.transaction_date = datetime(2023, 1, 1)
    txn1.transaction_type = "BUY"
    txn1.quantity = Decimal("10")
    txn1.price_per_unit = Decimal("1000") # 10,000 invested

    with patch(
        "app.crud.transaction.get_multi_by_portfolio",
        return_value=[txn1],
    ):
        # Mock empty history for RF fallback logic
        mock_financial_service.yfinance_provider.get_index_history.return_value = {}
        with patch("app.crud.analytics.get_portfolio_analytics", return_value=None):
            result = benchmark_service.calculate_benchmark_performance(
                "pf_id", benchmark_mode="single", risk_free_rate=7.0
            )

            assert "risk_free_xirr" in result
            assert round(result["risk_free_xirr"], 2) == 0.07
            assert len(result["chart_data"]) > 0

            # First day should have 10000 RF value
            assert result["chart_data"][0]["risk_free_value"] == 10000.0

            # End day should be > 10000
            last_value = result["chart_data"][-1]["risk_free_value"]
            days_passed = (date.today() - date(2023, 1, 1)).days
            expected_val = 10000 * (1.07 ** (days_passed/365))
            assert abs(last_value - expected_val) < 100 # Allow some rounding difference

def test_hybrid_benchmark_blended_values(
    benchmark_service, mock_db, mock_financial_service
):
    mock_financial_service.yfinance_provider = MagicMock()
    txn1 = MagicMock()
    txn1.transaction_date = datetime(2023, 1, 1)
    txn1.transaction_type = "BUY"
    txn1.quantity = Decimal("100")
    txn1.price_per_unit = Decimal("100") # 10,000 invested

    start_date = date(2023, 1, 1)
    today = date.today()

    # Nifty goes up 20% (100 -> 120)
    # Debt goes up 10% (100 -> 110)
    def mock_get_history(ticker, sd, ed):
        if ticker == "^NSEI":
            return {start_date.isoformat(): 100.0, today.isoformat(): 120.0}
        if ticker == "^CRSLDX":
            return {start_date.isoformat(): 100.0, today.isoformat(): 110.0}
        return {}

    yf = mock_financial_service.yfinance_provider
    yf.get_index_history.side_effect = mock_get_history

    with patch("app.crud.transaction.get_multi_by_portfolio", return_value=[txn1]):
        with patch("app.crud.analytics.get_portfolio_analytics", return_value=None):
            result = benchmark_service.calculate_benchmark_performance(
                "pf_id", benchmark_mode="hybrid", hybrid_preset="BALANCED_50_50"
            )

            assert len(result["chart_data"]) > 0
            last_point = result["chart_data"][-1]

            # Initial investment 10,000. 50% Nifty (5k -> 6k), 50% Debt (5k -> 5.5k)
            # Total expected final value: 11,500
            assert last_point["invested_amount"] == 10000.0
            assert abs(last_point["benchmark_value"] - 11500.0) < 50

def test_hybrid_benchmark_debt_fallback(
    benchmark_service, mock_db, mock_financial_service
):
    mock_financial_service.yfinance_provider = MagicMock()
    # Test when debt index history is empty, it falls back to growing at risk_free_rate
    txn1 = MagicMock()
    txn1.transaction_date = datetime(2023, 1, 1)
    txn1.transaction_type = "BUY"
    txn1.quantity = Decimal("100")
    txn1.price_per_unit = Decimal("100") # 10,000 invested

    start_date = date(2023, 1, 1)
    today = date.today()

    def mock_get_history(ticker, sd, ed):
        if ticker == "^NSEI":
            return {start_date.isoformat(): 100.0, today.isoformat(): 100.0} # Flat
        return {} # Debt is missing

    yf = mock_financial_service.yfinance_provider
    yf.get_index_history.side_effect = mock_get_history

    with patch("app.crud.transaction.get_multi_by_portfolio", return_value=[txn1]):
        with patch("app.crud.analytics.get_portfolio_analytics", return_value=None):
            result = benchmark_service.calculate_benchmark_performance(
                "pf_id",
                benchmark_mode="hybrid",
                hybrid_preset="BALANCED_50_50",
                risk_free_rate=7.0,
            )

            assert len(result["chart_data"]) > 0
            last_point = result["chart_data"][-1]

            # Nifty is flat (5k). Debt should grow at 7% from 5k.
            days_passed = (today - start_date).days
            expected_debt_grown = 5000 * (1.07 ** (days_passed/365))
            expected_total = 5000 + expected_debt_grown

            assert abs(last_point["benchmark_value"] - expected_total) < 50

def test_category_benchmark_splits_correctly(
    benchmark_service, mock_db, mock_financial_service
):
    mock_financial_service.yfinance_provider = MagicMock()
    txn_equity = MagicMock()
    txn_equity.transaction_date = datetime(2023, 1, 1)
    txn_equity.transaction_type = "BUY"
    txn_equity.quantity = Decimal("10")
    txn_equity.price_per_unit = Decimal("100") # 1000
    txn_equity.asset_id = "asset_eq"

    txn_debt = MagicMock()
    txn_debt.transaction_date = datetime(2023, 1, 1)
    txn_debt.transaction_type = "BUY"
    txn_debt.quantity = Decimal("1")
    txn_debt.price_per_unit = Decimal("5000") # 5000
    txn_debt.asset_id = "asset_debt"

    def mock_get_history(ticker, sd, ed):
        return {date(2023, 1, 1).isoformat(): 100.0, date.today().isoformat(): 110.0}

    yf = mock_financial_service.yfinance_provider
    yf.get_index_history.side_effect = mock_get_history

    mock_asset_eq = MagicMock()
    mock_asset_eq.id = "asset_eq"
    mock_asset_eq.asset_type = "Mutual Fund"

    mock_asset_debt = MagicMock()
    mock_asset_debt.id = "asset_debt"
    mock_asset_debt.asset_type = "FIXED_DEPOSIT"

    with patch(
        "app.crud.transaction.get_multi_by_portfolio",
        return_value=[txn_equity, txn_debt],
    ):
        with patch(
            "app.crud.asset.get_multi_by_portfolio",
            return_value=[
                mock_asset_eq, mock_asset_debt,
            ],
        ):
            with patch("app.crud.analytics.get_portfolio_analytics", return_value=None):
                result = benchmark_service.calculate_benchmark_performance(
                    "pf_id", benchmark_mode="category"
                )

                assert "category_data" in result
                cat_data = result["category_data"]

                assert "equity" in cat_data
                assert "debt" in cat_data

                # Equity should only sum the 1000 investment
                assert cat_data["equity"]["chart_data"][-1]["invested_amount"] == 1000.0

                # Debt should only sum the 5000 investment
                assert cat_data["debt"]["chart_data"][-1]["invested_amount"] == 5000.0


def test_benchmark_outflows_and_withdrawals(
    benchmark_service, mock_db, mock_financial_service
):
    """Test that SELL and WITHDRAWAL reduce benchmark units correctly."""
    mock_financial_service.yfinance_provider = MagicMock()

    # 1. BUY transaction
    txn1 = MagicMock()
    txn1.transaction_date = datetime(2023, 1, 1)
    txn1.transaction_type = "BUY"
    txn1.quantity = Decimal("100")
    txn1.price_per_unit = Decimal("100")  # 10,000 INR
    txn1.details = {}

    # 2. SELL transaction (outflow of 5,000 INR)
    txn2 = MagicMock()
    txn2.transaction_date = datetime(2023, 3, 1)
    txn2.transaction_type = "SELL"
    txn2.quantity = Decimal("50")
    txn2.price_per_unit = Decimal("100")  # 5,000 INR
    txn2.details = {}

    # 3. WITHDRAWAL transaction (outflow of 2,000 INR)
    txn3 = MagicMock()
    txn3.transaction_date = datetime(2023, 5, 1)
    txn3.transaction_type = "WITHDRAWAL"
    txn3.quantity = Decimal("20")
    txn3.price_per_unit = Decimal("100")  # 2,000 INR
    txn3.details = {}

    today = date.today()

    # Index is flat at 100.0 throughout the period
    index_history = {
        date(2023, 1, 1).isoformat(): 100.0,
        date(2023, 3, 1).isoformat(): 100.0,
        date(2023, 5, 1).isoformat(): 100.0,
        today.isoformat(): 100.0,
    }
    yf = mock_financial_service.yfinance_provider
    yf.get_index_history.return_value = index_history

    with patch(
        "app.crud.transaction.get_multi_by_portfolio",
        return_value=[txn1, txn2, txn3],
    ):
        with patch("app.crud.analytics.get_portfolio_analytics", return_value=None):
            result = benchmark_service.calculate_benchmark_performance("pf_id")

            # Initial: 10,000 invested. Units: 10,000 / 100 = 100 units.
            # SELL (Mar 1): 5,000 / 10,000 = 0.5 ratio. Units reduced by 50%.
            # Remaining: 50 units. Value: 5,000. Invested amount = 5,000.
            # WITHDRAWAL (May 1): 2,000 / 5,000 = 0.4 ratio. Units reduced by 40%.
            # Remaining: 30 units. Value: 3,000. Invested amount = 3,000.
            chart = result["chart_data"]

            # Find Mar 1 point
            mar_point = [p for p in chart if p["date"] == "2023-03-01"][0]
            assert mar_point["invested_amount"] == 5000.0
            assert mar_point["benchmark_value"] == 5000.0

            # Find May 1 point
            may_point = [p for p in chart if p["date"] == "2023-05-01"][0]
            assert may_point["invested_amount"] == 3000.0
            assert may_point["benchmark_value"] == 3000.0


def test_benchmark_all_transaction_types(
    benchmark_service, mock_db, mock_financial_service
):
    """Test that all transaction types are handled or ignored properly."""
    mock_financial_service.yfinance_provider = MagicMock()

    # Create one of each transaction type
    types = [
        # Inflows (BUY_TYPES)
        "BUY", "DEPOSIT", "RSU_VEST", "ESPP_PURCHASE", "CONTRIBUTION",
        # Outflows
        "SELL", "WITHDRAWAL", "DIVIDEND", "COUPON",
        # Others (Ignored by benchmark service)
        "BONUS", "SPLIT"
    ]

    txns = []
    for idx, t_type in enumerate(types):
        txn = MagicMock()
        txn.transaction_date = datetime(2023, 1, idx + 1)
        txn.transaction_type = t_type
        txn.quantity = Decimal("10")
        txn.price_per_unit = Decimal("100")  # 1,000 INR each
        txn.details = {}
        txns.append(txn)

    index_history = {
        date(2023, 1, i + 1).isoformat(): 100.0 for i in range(len(types))
    }
    index_history[date.today().isoformat()] = 100.0
    yf = mock_financial_service.yfinance_provider
    yf.get_index_history.return_value = index_history

    with patch(
        "app.crud.transaction.get_multi_by_portfolio", return_value=txns
    ):
        with patch("app.crud.analytics.get_portfolio_analytics", return_value=None):
            result = benchmark_service.calculate_benchmark_performance("pf_id")
            chart = result["chart_data"]

            # Let's verify each step's invested amount
            # Jan 1: BUY (+1000) -> 1000
            p1 = [p for p in chart if p["date"] == "2023-01-01"][0]
            assert p1["invested_amount"] == 1000.0

            # Jan 2: DEPOSIT (+1000) -> 2000
            p2 = [p for p in chart if p["date"] == "2023-01-02"][0]
            assert p2["invested_amount"] == 2000.0

            # Jan 3: RSU_VEST (+1000) -> 3000
            p3 = [p for p in chart if p["date"] == "2023-01-03"][0]
            assert p3["invested_amount"] == 3000.0

            # Jan 4: ESPP_PURCHASE (+1000) -> 4000
            p4 = [p for p in chart if p["date"] == "2023-01-04"][0]
            assert p4["invested_amount"] == 4000.0

            # Jan 5: CONTRIBUTION (+1000) -> 5000
            p5 = [p for p in chart if p["date"] == "2023-01-05"][0]
            assert p5["invested_amount"] == 5000.0

            # Jan 6: SELL (-1000) -> 4000
            p6 = [p for p in chart if p["date"] == "2023-01-06"][0]
            assert p6["invested_amount"] == 4000.0

            # Jan 7: WITHDRAWAL (-1000) -> 3000
            p7 = [p for p in chart if p["date"] == "2023-01-07"][0]
            assert p7["invested_amount"] == 3000.0

            # Jan 8: DIVIDEND -> doesn't change invested_amount, only reduces value.
            # Invested amount remains 3000.0
            p8 = [p for p in chart if p["date"] == "2023-01-08"][0]
            assert p8["invested_amount"] == 3000.0

            # Jan 9: COUPON -> doesn't change invested_amount. Remains 3000.0
            p9 = [p for p in chart if p["date"] == "2023-01-09"][0]
            assert p9["invested_amount"] == 3000.0

            # Jan 10: BONUS -> ignored completely. Invested amount remains 3000.0
            p10 = [p for p in chart if p["date"] == "2023-01-10"][0]
            assert p10["invested_amount"] == 3000.0

            # Jan 11: SPLIT -> ignored completely. Invested amount remains 3000.0
            p11 = [p for p in chart if p["date"] == "2023-01-11"][0]
            assert p11["invested_amount"] == 3000.0


def test_synthetic_transactions_generation_and_processing(
    benchmark_service, mock_db, mock_financial_service
):
    """Test generating synthetic transactions for FDs and RDs."""
    # Create mock FD
    fd = MagicMock()
    fd.start_date = date(2023, 1, 1)
    fd.maturity_date = date(2023, 12, 31)
    fd.principal_amount = Decimal("10000")
    fd.interest_rate = 8.0
    fd.interest_payout = "PAYOUT"
    fd.compounding_frequency = "SEMI-ANNUALLY"

    # Create mock RD
    rd = MagicMock()
    rd.start_date = date(2023, 6, 1)
    rd.monthly_installment = Decimal("1000")
    rd.tenure_months = 6
    rd.interest_rate = 6.0

    mock_db.query = MagicMock()

    fd_crud_path = "app.crud.fixed_deposit.get_multi_by_portfolio"
    rd_crud_path = "app.crud.recurring_deposit.get_multi_by_portfolio"
    calc_fd_path = "app.services.benchmark_service._calculate_fd_current_value"
    calc_rd_path = "app.services.benchmark_service._calculate_rd_value_at_date"

    with patch(fd_crud_path, return_value=[fd]):
        with patch(rd_crud_path, return_value=[rd]):
            with patch(calc_fd_path, return_value=Decimal("10800")):
                with patch(calc_rd_path, return_value=Decimal("6100")):
                    txns = benchmark_service._generate_synthetic_transactions(
                        "pf_id"
                    )

                    # Verify FD transactions:
                    # 1. BUY principal_amount on 2023-01-01
                    # 2. SEMI-ANNUALLY payouts on 2023-07-01 (400 DIVIDEND)
                    # 3. SELL maturity_value on 2023-12-31

                    # Verify RD transactions:
                    # 1. BUY monthly_installment for 6 months (06-01 to 11-01)
                    # 2. SELL maturity_value on maturity_date (2023-12-01)

                    buy_txns = [t for t in txns if t.transaction_type == "BUY"]
                    sell_txns = [t for t in txns if t.transaction_type == "SELL"]
                    div_txns = [
                        t for t in txns if t.transaction_type == "DIVIDEND"
                    ]

                    assert len(buy_txns) == 7  # 1 FD + 6 RD
                    assert len(sell_txns) == 2  # 1 FD + 1 RD
                    assert len(div_txns) == 1   # FD payout on 2023-07-01

                    # Check values
                    fd_buy = [
                        t for t in buy_txns
                        if t.transaction_date == datetime(2023, 1, 1)
                    ][0]
                    assert fd_buy.price_per_unit == Decimal("10000")

                    fd_div = [
                        t for t in div_txns
                        if t.transaction_date == datetime(2023, 7, 1)
                    ][0]
                    assert fd_div.price_per_unit == Decimal("400")

                    fd_sell = [
                        t for t in sell_txns
                        if t.transaction_date == datetime(2023, 12, 31)
                    ][0]
                    assert fd_sell.price_per_unit == Decimal("10800")


def test_benchmark_invested_amount_clamping(
    benchmark_service, mock_db, mock_financial_service
):
    """Test that invested_amount is clamped to zero when assets are sold."""
    mock_financial_service.yfinance_provider = MagicMock()

    # 1. BUY transaction for 1,000 INR
    txn1 = MagicMock()
    txn1.transaction_date = datetime(2023, 1, 1)
    txn1.transaction_type = "BUY"
    txn1.quantity = Decimal("10")
    txn1.price_per_unit = Decimal("100")
    txn1.details = {}

    # 2. SELL transaction for 1,500 INR (exceeds invested amount)
    txn2 = MagicMock()
    txn2.transaction_date = datetime(2023, 2, 1)
    txn2.transaction_type = "SELL"
    txn2.quantity = Decimal("10")
    txn2.price_per_unit = Decimal("150")
    txn2.details = {}

    today = date.today()

    index_history = {
        date(2023, 1, 1).isoformat(): 100.0,
        date(2023, 2, 1).isoformat(): 150.0,
        today.isoformat(): 150.0,
    }
    yf = mock_financial_service.yfinance_provider
    yf.get_index_history.return_value = index_history

    with patch(
        "app.crud.transaction.get_multi_by_portfolio", return_value=[txn1, txn2]
    ):
        with patch("app.crud.analytics.get_portfolio_analytics", return_value=None):
            result = benchmark_service.calculate_benchmark_performance("pf_id")
            chart = result["chart_data"]

            # Find Feb 1 point
            feb_point = [p for p in chart if p["date"] == "2023-02-01"][0]
            # Invested amount should be clamped to 0
            assert feb_point["invested_amount"] == 0.0

