import io
import zipfile
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.cache.base import CacheClient
from app.services.providers.nse_bhavcopy_provider import NseBhavcopyProvider

# Sample data mimicking the new Bhavcopy CSV format
SAMPLE_BHAVCOPY_CSV = """TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,SctySrs,XpryDt,StrkPric,OptnTp,OpnPric,HghPric,LwPric,ClsPric,LastPric,PrvsClsgPric,TtlTradgVol,TtlTrfVal,TtlNbOfTxsExctd\r
2025-10-22,2025-10-22,CM,NSE,STK,2885,INE002A01018,RELIANCE,EQ,,,,"2800","2850","2790","2845.50","2845.00","2800.00",1000,2845500,100\r
2025-10-22,2025-10-22,CM,NSE,STK,11536,INE467B01029,TCS,EQ,,,,"3500","3520","3490","3510.00","3510.00","3500.00",500,1755000,50\r
2025-10-22,2025-10-22,CM,NSE,STK,1594,INE009A01021,INFY,BE,,,,"1500","1510","1495","1505.00","1505.00","1500.00",200,301000,20\r
2025-10-22,2025-10-22,CM,NSE,STK,1270,INE062A01020,SBIN,EQ,,,,"600","610","595","605.75","605.00","600.00",2000,1211500,150\r
"""


@pytest.fixture
def mock_cache_client():
    """Fixture for a mocked cache client."""
    client = MagicMock(spec=CacheClient)
    client.get_json.return_value = None
    client.set_json.return_value = None
    return client


def _create_zip_in_memory(csv_content: str, csv_filename: str) -> bytes:
    """Helper to create a zip archive in memory."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(csv_filename, csv_content)
    return zip_buffer.getvalue()

@patch("app.services.providers.nse_bhavcopy_provider.httpx.Client")
def test_fetch_and_parse_bhavcopy_success(mock_httpx_client_class):
    """Test that the Bhavcopy is fetched, unzipped, and parsed correctly."""
    today = date(2025, 10, 22)
    csv_filename = f"BhavCopy_NSE_CM_0_0_0_{today.strftime('%Y%m%d')}_F_0000.csv"
    zip_content = _create_zip_in_memory(SAMPLE_BHAVCOPY_CSV, csv_filename)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_content
    mock_response.raise_for_status.return_value = None

    mock_client_instance = MagicMock()
    mock_client_instance.get.return_value = mock_response
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client_instance

    provider = NseBhavcopyProvider(cache_client=None)
    data = provider._fetch_and_parse_bhavcopy(for_date=today) # type: ignore

    assert "RELIANCE" in data
    assert data["RELIANCE"]["current_price"] == Decimal("2845.50")
    assert data["RELIANCE"]["previous_close"] == Decimal("2800.00")
    assert "TCS" in data
    # Should now include 'BE' series as it's not in the excluded list
    assert "INFY" in data
    assert len(data) == 4


@patch("app.services.providers.nse_bhavcopy_provider.httpx.Client")
def test_fetch_bhavcopy_with_fallback(mock_httpx_client_class):
    """Test that the provider falls back to previous days if today's is not found."""
    today = date(2025, 10, 22)
    yesterday = today - timedelta(days=1)
    csv_filename = f"BhavCopy_NSE_CM_0_0_0_{yesterday.strftime('%Y%m%d')}_F_0000.csv"
    zip_content = _create_zip_in_memory(SAMPLE_BHAVCOPY_CSV, csv_filename)

    # Mock responses: 404 for today, 200 for yesterday
    mock_response_404 = MagicMock(status_code=404)
    mock_response_200 = MagicMock(status_code=200, content=zip_content)

    mock_client_instance = MagicMock()
    mock_client_instance.get.side_effect = [mock_response_404, mock_response_200]
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client_instance

    provider = NseBhavcopyProvider(cache_client=None)
    data = provider._fetch_and_parse_bhavcopy(for_date=today) # type: ignore

    assert mock_client_instance.get.call_count == 2
    assert "RELIANCE" in data
    assert len(data) == 4


def test_get_current_prices(mock_cache_client):
    """Test that get_current_prices correctly filters from the full bhavcopy data."""
    provider = NseBhavcopyProvider(cache_client=mock_cache_client)
    mock_bhavcopy_data = {
        "RELIANCE": {
            "current_price": Decimal("2845.50"),
            "previous_close": Decimal("2800.00"),
        },
        "TCS": {
            "current_price": Decimal("3510.00"),
            "previous_close": Decimal("3500.00"),
        },
    }

    # Patch the internal method that fetches/caches the full data
    with patch.object(provider, "_get_bhavcopy_data", return_value=mock_bhavcopy_data):
        assets_to_price = [
            {"ticker_symbol": "RELIANCE"},
            {"ticker_symbol": "NONEXISTENT"},
        ]
        prices = provider.get_current_prices(assets_to_price) # type: ignore

        assert "RELIANCE" in prices
        assert "NONEXISTENT" not in prices
        assert len(prices) == 1
        assert prices["RELIANCE"]["current_price"] == Decimal("2845.50")


def test_caching_mechanism(mock_cache_client):
    """Test that data is fetched once and then served from cache."""
    provider = NseBhavcopyProvider(cache_client=mock_cache_client)

    # Simulate fresh data to be cached
    fresh_data = {
        "RELIANCE": {
            "current_price": Decimal("2845.50"),
            "previous_close": Decimal("2800.00"),
        }
    }
    # The data that will be set in the cache is serialized (strings)
    serialized_data = {"RELIANCE": {"current_price": "2845.50", "previous_close": "2800.00"}}

    with patch.object(provider, "_fetch_and_parse_bhavcopy", return_value=fresh_data) as mock_fetch:
        # 1. First call: cache is empty, should fetch and set cache
        provider._get_bhavcopy_data() # type: ignore
        mock_cache_client.get_json.assert_called_once()
        mock_fetch.assert_called_once()
        mock_cache_client.set_json.assert_called_once_with(
            f"bhavcopy_data:{date.today().isoformat()}", # type: ignore
            serialized_data,
            expire=43200
        )

        # 2. Second call: simulate cache hit
        mock_cache_client.get_json.return_value = serialized_data
        provider._get_bhavcopy_data() # type: ignore

        # Assert that get_json was called again, but fetch was not.
        assert mock_cache_client.get_json.call_count == 2
        mock_fetch.assert_called_once()