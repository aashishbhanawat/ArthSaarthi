from fastapi import HTTPException


class FinancialDataService:
    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url

    async def lookup_ticker(self, ticker_symbol: str) -> dict:
        """
        Looks up a ticker symbol from an external API.
        This is a mock implementation.
        In a real scenario, this would make an HTTP request to the external service.
        """
        # Mock data for demonstration
        mock_database = {
            "AAPL": {"name": "Apple Inc.", "asset_type": "STOCK", "currency": "USD"},
            "GOOGL": {"name": "Alphabet Inc.", "asset_type": "STOCK", "currency": "USD"},
        }

        if ticker_symbol.upper() in mock_database:
            return mock_database[ticker_symbol.upper()]

        raise HTTPException(status_code=404, detail="Ticker symbol not found in external service")

    def get_asset_price(self, ticker_symbol: str) -> dict:
        """
        Gets the current price for a ticker symbol.
        This is a mock implementation.
        """
        # Mock data for demonstration
        mock_prices = {
            "AAPL": {"price": 150.0},
            "GOOG": {"price": 2800.0},
            "MSFT": {"price": 305.0},
            "BTC": {"price": 45000.0},
            "TSLA": {"price": 255.0},
        }
        return mock_prices.get(ticker_symbol.upper(), {"price": 0.0})