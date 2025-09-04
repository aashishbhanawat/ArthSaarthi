from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional


class MockFinancialDataService:
    """
    A mock financial data service that returns predictable data for testing.
    """

    MOCK_PRICES = {
        "AAPL": {
            "current_price": Decimal("175.00"),
            "previous_close": Decimal("170.00"),
        },
        "GOOGL": {
            "current_price": Decimal("150.00"),
            "previous_close": Decimal("148.00"),
        },
        "MSFT": {
            "current_price": Decimal("300.00"),
            "previous_close": Decimal("295.00"),
        },
        "RELIANCE": {
            "current_price": Decimal("2550.00"),
            "previous_close": Decimal("2540.00"),
        },
        "TCS": {
            "current_price": Decimal("3500.00"),
            "previous_close": Decimal("3490.00")
        },
        "UPDATE": {
            "current_price": Decimal("110.00"),
            "previous_close": Decimal("105.00"),
        },
        "DELETE": {
            "current_price": Decimal("50.00"),
            "previous_close": Decimal("51.00")
        },
        "CALC1": {
            "current_price": Decimal("110.0"),
            "previous_close": Decimal("109.0")
        },
        "XIRRTEST": {
            "current_price": Decimal("130.0"),
            "previous_close": Decimal("129.0"),
        },
        "ASSET1": {
            "current_price": Decimal("100.00"),
            "previous_close": Decimal("99.00")
        },
        "ASSET2": {
            "current_price": Decimal("200.00"),
            "previous_close": Decimal("198.00"),
        },
        "TXN1": {
            "current_price": Decimal("100.00"),
            "previous_close": Decimal("99.00")
        },
        "TXN2": {
            "current_price": Decimal("200.00"),
            "previous_close": Decimal("198.00")}
        ,
    }

    MOCK_MF_SEARCH_RESULTS = [
        {
            "ticker_symbol": "100033",
            "name": "Axis Bluechip Fund - Direct Plan - Growth",
            "asset_type": "Mutual Fund",
        },
        {
            "ticker_symbol": "120503",
            "name": "HDFC Index Fund - S&P BSE Sensex Plan - Direct Plan",
            "asset_type": "Mutual Fund",
        },
    ]

    MOCK_MF_PRICES = {
        "100033": {
            "current_price": Decimal("58.98"),
            "previous_close": Decimal("58.00"),
        },
        "120503": {
            "current_price": Decimal("654.32"),
            "previous_close": Decimal("650.00"),
        },
    }

    def get_current_prices(
        self, assets: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Decimal]]:
        results = {}
        for asset in assets:
            ticker = asset["ticker_symbol"]
            if ticker in self.MOCK_PRICES:
                results[ticker] = self.MOCK_PRICES[ticker]
            elif ticker in self.MOCK_MF_PRICES:
                results[ticker] = self.MOCK_MF_PRICES[ticker]
        return results

    def get_historical_prices(
        self, assets: List[Dict[str, Any]], start_date: date, end_date: date
    ) -> Dict[str, Dict[date, Decimal]]:
        # This can be expanded if tests need more complex historical data
        return {}

    def get_asset_details(
        self, ticker_symbol: str, asset_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        # Make the mock more robust. First, check if the ticker is a known
        # mutual fund. This avoids relying on the asset_type being passed
        # correctly through all layers.
        for fund in self.MOCK_MF_SEARCH_RESULTS:
            if fund["ticker_symbol"] == ticker_symbol:
                # Return a structure consistent with what the real service would provide
                return {
                    "name": fund["name"],
                    "asset_type": "Mutual Fund",
                    "exchange": "AMFI",
                    "currency": "INR",
                    "isin": f"INF{ticker_symbol}DUMMY",  # Mock ISIN
                }

        # If it's not a mutual fund, check if it's a known stock.
        if ticker_symbol in self.MOCK_PRICES:
            return {
                "name": f"{ticker_symbol} Inc.",
                "asset_type": "Stock",
                "exchange": "NASDAQ",
                "currency": "USD",
            }
        return None

    def search_mutual_funds(self, query: str) -> List[Dict[str, Any]]:
        query = query.lower()
        return [
            fund
            for fund in self.MOCK_MF_SEARCH_RESULTS
            if query in fund["name"].lower()
        ]
