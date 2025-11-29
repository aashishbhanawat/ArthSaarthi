
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.cache.factory import get_cache_client
from app.main import app

client = TestClient(app)
# We need to mock the cache client so we can control its behavior in tests
cache_client_mock = MagicMock()


# This fixture will run before each test function, ensuring a clean state
@pytest.fixture(autouse=True)
def override_cache_dependency():
    # This is where the magic happens: we override the dependency
    app.dependency_overrides[get_cache_client] = lambda: cache_client_mock
    # It's good practice to reset the mock before each test
    cache_client_mock.reset_mock()
    yield
    # Clean up the override after the test is done
    app.dependency_overrides = {}


@patch("yfinance.Ticker")
def test_get_fx_rate_success_no_cache(mock_ticker, override_cache_dependency):
    # Arrange
    # Simulate that the cache does not have the value
    cache_client_mock.get.return_value = None
    mock_ticker.return_value.history.return_value = pd.DataFrame({"Close": [83.50]})

    # Act
    response = client.get("/api/v1/fx-rate?source=USD&to=INR&date=2025-11-25")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"rate": 83.50}
    # Verify that we tried to get from cache and then set the new value
    cache_client_mock.get.assert_called_once_with("fx-rate-USD-INR-2025-11-25")
    cache_client_mock.set.assert_called_once()
    # Verify that yfinance was called because the cache missed
    mock_ticker.assert_called_once()


def test_get_fx_rate_success_with_cache(override_cache_dependency):
    # Arrange
    # Simulate that the cache returns a value
    cache_client_mock.get.return_value = 83.50

    # Act
    response = client.get("/api/v1/fx-rate?source=USD&to=INR&date=2025-11-25")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"rate": 83.50}
    # Verify that we only tried to get from cache
    cache_client_mock.get.assert_called_once_with("fx-rate-USD-INR-2025-11-25")
    # Verify that we did NOT set a new value or call yfinance
    cache_client_mock.set.assert_not_called()


@patch("yfinance.Ticker")
def test_get_fx_rate_yfinance_fails(mock_ticker, override_cache_dependency):
    # Arrange
    cache_client_mock.get.return_value = None
    # Simulate yfinance returning an empty DataFrame
    mock_ticker.return_value.history.return_value = pd.DataFrame()

    # Act
    response = client.get("/api/v1/fx-rate?source=USD&to=INR&date=2025-11-25")

    # Assert
    assert response.status_code == 404
    assert response.json() == {"error": "Rate not found"}
    cache_client_mock.get.assert_called_once()
    # We should not try to set a value in the cache if yfinance fails
    cache_client_mock.set.assert_not_called()


@patch("yfinance.Ticker")
def test_get_fx_rate_not_found(mock_ticker, override_cache_dependency):
    # Arrange
    cache_client_mock.get.return_value = None
    mock_ticker.return_value.history.return_value = pd.DataFrame()

    # Act
    response = client.get("/api/v1/fx-rate?source=XXX&to=YYY&date=2025-11-25")

    # Assert
    assert response.status_code == 404
    assert response.json() == {"error": "Rate not found"}
    cache_client_mock.get.assert_called_once()
    cache_client_mock.set.assert_not_called()
