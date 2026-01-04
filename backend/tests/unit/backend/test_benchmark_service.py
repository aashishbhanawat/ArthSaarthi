import pytest
from unittest.mock import MagicMock, Mock, patch
from datetime import date, datetime, timedelta
from decimal import Decimal

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

def test_calculate_benchmark_performance_success(benchmark_service, mock_db, mock_financial_service):
    # Mock Transactions
    txn1 = MagicMock()
    txn1.transaction_date = datetime(2023, 1, 1)
    txn1.transaction_type = "BUY"
    txn1.amount = Decimal("10000")
    
    txn2 = MagicMock()
    txn2.transaction_date = datetime(2023, 6, 1)
    txn2.transaction_type = "BUY"
    txn2.amount = Decimal("5000")
    
    with patch("app.crud.transaction.get_multi_by_portfolio", return_value=[txn1, txn2]):
        # Mock Index History
        # index 100 on Jan 1, 110 on Jun 1, 120 Today
        start_date = date(2023, 1, 1)
        today = date.today()
        
        index_history = {
            start_date.isoformat(): 100.0,
            date(2023, 6, 1).isoformat(): 110.0,
            today.isoformat(): 120.0,
        }
        mock_financial_service.yfinance_provider.get_index_history.return_value = index_history
        
        # Mock Portfolio Analytics
        mock_pf_analytics = MagicMock()
        mock_pf_analytics.xirr = 10.5
        with patch("app.crud.analytics.get_portfolio_analytics", return_value=mock_pf_analytics):
            
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

