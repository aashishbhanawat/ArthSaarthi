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
