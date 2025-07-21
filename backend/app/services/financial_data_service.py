class FinancialDataService:
    def __init__(self, api_key: str, api_url: str):
        # In a real app, these would be used to connect to the service
        self.api_key = api_key
        self.api_url = api_url

    def get_asset_price(self, ticker_symbol: str) -> float:
        # Mock implementation
        if ticker_symbol.upper() == "COAL":
            return 150.0
        if ticker_symbol.upper() == "GOOGL":
            return 2800.0
        raise Exception(f"Could not retrieve price for {ticker_symbol}")

    def get_asset_details(self, ticker_symbol: str) -> dict | None:
        # Mock implementation for asset lookup
        MOCK_ASSETS = {
            "AAPL": {"name": "Apple Inc.", "asset_type": "STOCK", "currency": "USD"},
            "GOOGL": {"name": "Alphabet Inc.", "asset_type": "STOCK", "currency": "USD"},
        }
        return MOCK_ASSETS.get(ticker_symbol.upper())