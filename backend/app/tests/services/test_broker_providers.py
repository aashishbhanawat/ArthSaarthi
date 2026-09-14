from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.providers.icici_breeze_provider import IciciBreezeProvider


def test_icici_breeze_provider_login_url():
    url = IciciBreezeProvider.get_login_url("my_app_key_123")
    assert "API_KEY=my_app_key_123" in url


def test_icici_breeze_provider_get_prices():
    provider = IciciBreezeProvider(
        api_key="key_123",
        session_token="session_456",
        api_secret="secret_789",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "Success": [
            {
                "stock_code": "RELIANCE",
                "lTP": 2500.50,
                "previous_close": 2480.00,
            }
        ]
    }

    with patch("httpx.Client.get", return_value=mock_resp):
        assets = [{"ticker_symbol": "RELIANCE.NS", "exchange": "NSE"}]
        prices = provider.get_current_prices(assets)

        assert "RELIANCE.NS" in prices
        assert prices["RELIANCE.NS"]["current_price"] == Decimal("2500.5")
        assert prices["RELIANCE.NS"]["previous_close"] == Decimal("2480")


def test_icici_breeze_provider_unconfigured():
    provider = IciciBreezeProvider()
    assets = [{"ticker_symbol": "INFY.NS"}]
    prices = provider.get_current_prices(assets)
    assert prices == {}
