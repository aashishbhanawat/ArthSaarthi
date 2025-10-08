from unittest.mock import MagicMock, patch

import pytest

from app.cache.base import CacheClient
from app.services.financial_data_service import AmfiIndiaProvider

# Sample data mimicking the AMFI NAV text file format with shorter lines
SAMPLE_AMFI_DATA = """Scheme Code;ISIN;ISIN Reinvestment;Scheme Name;NAV;Date
119551;INF204K01282;INF204K01290;Aditya Birla Arbitrage Fund;25.61;21-Aug-2025
100033;INF090I01037;INF090I01045;Axis Bluechip Fund;58.98;21-Aug-2025
120503;INF846K01DP8;INF846K01DQ6;HDFC Index Fund - Sensex;654.32;21-Aug-2025
120504;INF846K01DR4;INF846K01DS2;HDFC Nifty 50 Index Fund;210.11;21-Aug-2025
"""

@pytest.fixture
def mock_httpx_client():
    with patch('httpx.Client') as mock_client_class:
        mock_response = MagicMock()
        mock_response.text = SAMPLE_AMFI_DATA
        mock_response.raise_for_status.return_value = None

        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response

        mock_client_class.return_value.__enter__.return_value = mock_client_instance
        yield mock_client_class

@pytest.fixture
def mock_cache_client():
    client = MagicMock(spec=CacheClient)
    client.get_json.return_value = None
    client.set_json.return_value = None
    return client

def test_fetch_and_parse_amfi_data(mock_httpx_client):
    """Test that the AMFI data is fetched and parsed correctly."""
    provider = AmfiIndiaProvider(cache_client=None)
    data = provider._fetch_and_parse_amfi_data()

    assert "100033" in data
    assert data["100033"]["scheme_name"] == "Axis Bluechip Fund"
    assert data["100033"]["nav"] == "58.98"
    assert data["100033"]["date"] == "2025-08-21"
    assert data["119551"]["isin"] == "INF204K01282"
    assert len(data) == 4

def test_get_all_nav_data_no_cache(mock_httpx_client):
    """Test getting all NAV data without caching."""
    provider = AmfiIndiaProvider(cache_client=None)
    data = provider.get_all_nav_data()

    assert "120503" in data
    mock_httpx_client.return_value.__enter__.return_value.get.assert_called_once()

def test_get_all_nav_data_with_caching(mock_httpx_client, mock_cache_client):
    """Test that data is fetched and then cached."""
    provider = AmfiIndiaProvider(cache_client=mock_cache_client)

    # First call: should fetch from HTTP and set cache
    data = provider.get_all_nav_data()
    assert "100033" in data
    mock_cache_client.get_json.assert_called_once_with("amfi_nav_data")
    mock_httpx_client.return_value.__enter__.return_value.get.assert_called_once()
    mock_cache_client.set_json.assert_called_once()

    # Second call: should get from cache
    mock_cache_client.get_json.return_value = data # Simulate cache hit
    provider.get_all_nav_data()
    # get_json is called again, but httpx.get is not
    assert mock_cache_client.get_json.call_count == 2
    mock_httpx_client.return_value.__enter__.return_value.get.assert_called_once()

def test_get_details_success(mock_httpx_client):
    """Test getting details for a valid MF scheme code."""
    provider = AmfiIndiaProvider(cache_client=None)
    details = provider.get_asset_details("100033")

    assert details is not None
    assert details["name"] == "Axis Bluechip Fund"
    assert details["asset_type"] == "Mutual Fund"
    assert details["exchange"] == "AMFI"
    assert details["currency"] == "INR"
    assert details["isin"] == "INF090I01037"

def test_get_details_not_found(mock_httpx_client):
    """Test getting details for an invalid MF scheme code."""
    provider = AmfiIndiaProvider(cache_client=None)
    details = provider.get_asset_details("999999")
    assert details is None

def test_search_funds(mock_httpx_client):
    """Test searching for funds by name and scheme code."""
    provider = AmfiIndiaProvider(cache_client=None)

    # Search by name part
    results_name = provider.search("axis bluechip")
    assert len(results_name) == 1
    assert results_name[0]["ticker_symbol"] == "100033"
    assert results_name[0]["name"] == "Axis Bluechip Fund"

    # Search by scheme code
    results_code = provider.search("12050")
    assert len(results_code) == 2 # 120503 and 120504

    # Search by common name part
    results_hdfc = provider.search("hdfc")
    assert len(results_hdfc) == 2

    # No results
    results_none = provider.search("nonexistentfund")
    assert len(results_none) == 0
