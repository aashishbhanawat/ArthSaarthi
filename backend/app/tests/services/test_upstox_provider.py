"""
Unit tests for UpstoxProvider and UpstoxMetadataService.
"""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.cache.base import CacheClient
from app.services.financial_data_service import FinancialDataService
from app.services.providers.upstox_provider import UpstoxProvider
from app.services.upstox_metadata_service import UpstoxMetadataService


@pytest.fixture
def mock_cache_client():
    client = MagicMock(spec=CacheClient)
    client.get_json.return_value = None
    client.set_json.return_value = None
    return client


def test_upstox_metadata_service_holiday_and_weekend_check():
    """Test weekend detection and holiday loading in UpstoxMetadataService."""
    metadata_service = UpstoxMetadataService(cache_client=None)

    # Saturday and Sunday checks
    saturday = date(2026, 8, 1)
    sunday = date(2026, 8, 2)
    monday = date(2026, 8, 3)

    assert metadata_service.is_market_closed(saturday) is True
    assert metadata_service.is_market_closed(sunday) is True

    # Inject mock holiday
    metadata_service._holidays = {date(2026, 8, 15)}
    metadata_service._loaded = True

    assert metadata_service.is_market_closed(date(2026, 8, 15)) is True
    assert metadata_service.is_market_closed(monday) is False


def test_upstox_metadata_service_instrument_key_resolution():
    """Test resolution of ISIN, tickers, and indices to Upstox instrument keys."""
    metadata_service = UpstoxMetadataService(cache_client=None)
    metadata_service._isin_to_key_map = {"INE002A01018": "NSE_EQ|INE002A01018"}
    metadata_service._symbol_to_key_map = {"RELIANCE": "NSE_EQ|INE002A01018"}
    metadata_service._loaded = True

    # ISIN resolution
    assert metadata_service.get_instrument_key("RELIANCE", "INE002A01018") == "NSE_EQ|INE002A01018"
    # Ticker resolution
    assert metadata_service.get_instrument_key("RELIANCE") == "NSE_EQ|INE002A01018"
    # Index resolution
    assert metadata_service.get_instrument_key("^NSEI") == "NSE_INDEX|Nifty 50"
    assert metadata_service.get_instrument_key("INDIAVIX") == "NSE_INDEX|India VIX"


@patch.object(UpstoxProvider, "_fetch_upstox_candles")
def test_upstox_provider_get_current_prices(mock_fetch, mock_cache_client):
    """Test fetching current price and previous close from UpstoxProvider."""
    provider = UpstoxProvider(cache_client=mock_cache_client)
    provider.metadata_service._isin_to_key_map = {"INE002A01018": "NSE_EQ|INE002A01018"}
    provider.metadata_service._loaded = True

    # Sample candle response: [timestamp, open, high, low, close, volume, oi]
    mock_fetch.return_value = [
        ["2026-07-31T00:00:00+05:30", 1300.0, 1320.0, 1290.0, 1315.5, 100000, 0],
        ["2026-07-30T00:00:00+05:30", 1280.0, 1305.0, 1275.0, 1298.0, 95000, 0],
    ]

    assets = [{"ticker_symbol": "RELIANCE", "isin": "INE002A01018", "asset_type": "STOCK"}]
    prices = provider.get_current_prices(assets)

    assert "RELIANCE" in prices
    assert prices["RELIANCE"]["current_price"] == Decimal("1315.5")
    assert prices["RELIANCE"]["previous_close"] == Decimal("1298.0")


@patch.object(UpstoxProvider, "_fetch_upstox_candles")
def test_upstox_provider_get_historical_prices(mock_fetch, mock_cache_client):
    """Test fetching historical OHLC prices from UpstoxProvider."""
    provider = UpstoxProvider(cache_client=mock_cache_client)
    provider.metadata_service._isin_to_key_map = {"INE002A01018": "NSE_EQ|INE002A01018"}
    provider.metadata_service._loaded = True

    mock_fetch.return_value = [
        ["2026-07-31T00:00:00+05:30", 1300.0, 1320.0, 1290.0, 1315.5, 100000, 0],
        ["2026-07-30T00:00:00+05:30", 1280.0, 1305.0, 1275.0, 1298.0, 95000, 0],
    ]

    assets = [{"ticker_symbol": "RELIANCE", "isin": "INE002A01018"}]
    history = provider.get_historical_prices(assets, date(2026, 7, 30), date(2026, 7, 31))

    assert "RELIANCE" in history
    assert history["RELIANCE"][date(2026, 7, 31)] == Decimal("1315.5")
    assert history["RELIANCE"][date(2026, 7, 30)] == Decimal("1298.0")


@patch.object(UpstoxProvider, "get_current_prices")
@patch("app.services.financial_data_service.YFinanceProvider.get_current_prices")
def test_financial_data_service_upstox_primary_with_yfinance_fallback(
    mock_yf_prices, mock_upstox_prices, mock_cache_client
):
    """Test that FinancialDataService uses Upstox as primary and falls back to yfinance if needed."""
    service = FinancialDataService(cache_client=mock_cache_client)

    # Upstox resolves RELIANCE, but fails to resolve AAPL (foreign stock)
    mock_upstox_prices.return_value = {
        "RELIANCE": {"current_price": Decimal("1315.5"), "previous_close": Decimal("1298.0")}
    }
    mock_yf_prices.return_value = {
        "AAPL": {"current_price": Decimal("220.0"), "previous_close": Decimal("218.0")}
    }

    assets = [
        {"ticker_symbol": "RELIANCE", "asset_type": "STOCK", "isin": "INE002A01018"},
        {"ticker_symbol": "AAPL", "asset_type": "STOCK", "isin": None},
    ]

    res = service.get_current_prices(assets)

    assert "RELIANCE" in res
    assert res["RELIANCE"]["current_price"] == Decimal("1315.5")
    assert "AAPL" in res
    assert res["AAPL"]["current_price"] == Decimal("220.0")
