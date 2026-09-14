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


def test_zerodha_kite_provider_login_url():
    from app.services.providers.zerodha_provider import ZerodhaKiteProvider
    url = ZerodhaKiteProvider.get_login_url("my_kite_key_123")
    assert "api_key=my_kite_key_123" in url


def test_zerodha_kite_provider_authenticate_request_token():
    from app.services.providers.zerodha_provider import ZerodhaKiteProvider
    provider = ZerodhaKiteProvider(api_key="key_123", api_secret="secret_456")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "success",
        "data": {"access_token": "valid_kite_access_token_789"}
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        res = provider.authenticate_request_token("req_token_000")
        assert res["success"] is True
        assert res["access_token"] == "valid_kite_access_token_789"


def test_zerodha_kite_provider_get_prices():
    from app.services.providers.zerodha_provider import ZerodhaKiteProvider
    provider = ZerodhaKiteProvider(api_key="key_123", access_token="access_456")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "success",
        "data": {
            "NSE:INFY": {
                "last_price": 1500.25,
                "ohlc": {"close": 1490.00}
            }
        }
    }

    with patch("httpx.Client.get", return_value=mock_resp):
        assets = [{"ticker_symbol": "INFY.NS", "exchange": "NSE"}]
        prices = provider.get_current_prices(assets)
        assert "INFY.NS" in prices
        assert prices["INFY.NS"]["current_price"] == Decimal("1500.25")
        assert prices["INFY.NS"]["previous_close"] == Decimal("1490")

